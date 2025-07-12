import os
import pickle
import math
from collections import defaultdict
import heapq
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .utils_spimi import preprocess
from storage.HeapFile import HeapFile
from .ExtendibleHashIndex import ExtendibleHashIndex
from storage.Record import Record


class SPIMIIndexer:
    def __init__(self, block_dir="index_blocks", index_table_name="inverted_index"):
        self.block_dir = block_dir
        self.index_table_name = index_table_name
        os.makedirs(self.block_dir, exist_ok=True)

    def build_index(self, table_name: str):
        self.doc_count = 0
        self._process_documents(table_name)
        full_index, document_norms = self._external_merge_blocks_with_tfidf()
        self._save_index_to_table(full_index, document_norms)
        self._clean_blocks()

    def _process_documents(self, table_name: str):
        heapfile: HeapFile = HeapFile(table_name)
        term_dict = defaultdict(lambda: defaultdict(int))
        block_number = 0
        memory_limit = 100 * 1024 * 1024  # 100 MB

        for doc_id, text in heapfile.iterate_text_documents():
            self.doc_count += 1
            tokens = preprocess(text)
            for token in tokens:
                term_dict[token][doc_id] += 1

                # Verificar uso de memoria
                if sys.getsizeof(term_dict) >= memory_limit:
                    self._dump_block(term_dict, block_number)
                    block_number += 1
                    term_dict.clear()

        if term_dict:
            self._dump_block(term_dict, block_number)

    def _dump_block(self, term_dict, block_number):
        path = os.path.join(self.block_dir, f"block_{block_number}.pkl")
        # Guardar los términos ordenados
        sorted_dict = dict(sorted(term_dict.items()))
        with open(path, "wb") as f:
            pickle.dump(sorted_dict, f)
        print(f"[SPIMI] Bloque {block_number} guardado con {len(sorted_dict)} términos.")

    def _external_merge_blocks_with_tfidf(self):
        """
        Realiza un merge externo ordenado entre bloques y calcula TF-IDF en el proceso.
        Ahora también calcula las normas de los documentos.
        Devuelve: (inverted_index, document_norms)
        """
        block_paths = [os.path.join(self.block_dir, f) for f in os.listdir(self.block_dir) if f.endswith(".pkl")]
        block_iters = []
        current_terms = {}
        heap = []
        N = self.doc_count
        merged_index = {}
        document_norms = defaultdict(float)  # {doc_id: suma_de_cuadrados_tfidf}

        # Inicializar iteradores de bloques (igual que antes)
        for i, path in enumerate(block_paths):
            with open(path, "rb") as f:
                block = pickle.load(f)
                block_iter = iter(block.items())
                block_iters.append(block_iter)
                try:
                    term, postings = next(block_iter)
                    heapq.heappush(heap, (term, i))
                    current_terms[i] = (term, postings)
                except StopIteration:
                    continue

        while heap:
            smallest_term, block_idx = heapq.heappop(heap)
            
            combined_postings = defaultdict(int)
            blocks_to_advance = []

            for i in list(current_terms.keys()):
                term, postings = current_terms[i]
                if term == smallest_term:
                    for doc_id, freq in postings.items():
                        combined_postings[doc_id] += freq
                    blocks_to_advance.append(i)
                    del current_terms[i]

            df_t = len(combined_postings)
            idf = math.log(N / df_t) if df_t and N > 0 else 0
            postings_tfidf = []
            
            for doc_id, freq in combined_postings.items():
                tfidf = round(freq * idf, 5)
                postings_tfidf.append((doc_id, tfidf))
                document_norms[doc_id] += tfidf ** 2  # Acumula el cuadrado para la norma
            
            merged_index[smallest_term] = postings_tfidf

            for i in blocks_to_advance:
                try:
                    term, postings = next(block_iters[i])
                    heapq.heappush(heap, (term, i))
                    current_terms[i] = (term, postings)
                except StopIteration:
                    pass

        # Calcular la raíz cuadrada para obtener las normas finales
        document_norms = {doc_id: math.sqrt(norm) for doc_id, norm in document_norms.items()}
        
        print(f"[SPIMI] Merge externo completado con {len(merged_index)} términos.")
        return merged_index, document_norms

    def _save_index_to_table(self, inverted_index, document_norms):
        """
        Guarda el índice invertido (con TF-IDF) y las normas en la tabla.
        """
        # Esquema para el índice invertido
        schema_idx = [("term", "50s"), ("postings", "text")]
        HeapFile.build_file(self.index_table_name, schema_idx, "term")
        heapfile_idx = HeapFile(self.index_table_name)

        for term, postings in inverted_index.items():
            postings_serialized = json.dumps(postings)
            record = Record(schema_idx, [term, postings_serialized])
            heapfile_idx.insert_record(record)

        # Esquema para las normas (nueva tabla)
        schema_norms = [("doc_id", "i"), ("norm", "f")]
        norms_table_name = f"{self.index_table_name}_norms"
        HeapFile.build_file(norms_table_name, schema_norms, "doc_id")
        heapfile_norms = HeapFile(norms_table_name)

        for doc_id, norm in document_norms.items():
            record = Record(schema_norms, [doc_id, norm])
            heapfile_norms.insert_record(record)

        # Crear índices hash
        ExtendibleHashIndex.build_index(
            self.index_table_name,
            lambda field_name: heapfile_idx.extract_index(field_name),
            "term"
        )
        ExtendibleHashIndex.build_index(
            norms_table_name,
            lambda field_name: heapfile_norms.extract_index(field_name),
            "doc_id"
        )
        
        print(f"[SPIMI] Índice TF-IDF guardado en '{self.index_table_name}'")
        print(f"[SPIMI] Normas de documentos guardadas en '{norms_table_name}'")

    def _clean_blocks(self):
        """
        Elimina todos los archivos de bloques temporales.
        """
        for fname in os.listdir(self.block_dir):
            os.remove(os.path.join(self.block_dir, fname))
        os.rmdir(self.block_dir)
        print("[SPIMI] Bloques temporales eliminados.")
