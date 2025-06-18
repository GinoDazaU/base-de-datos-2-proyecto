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

MAX_TERMS_PER_BLOCK = 100

class SPIMIIndexer:
    def __init__(self, block_dir="index_blocks", index_table_name="inverted_index"):
        self.block_dir = block_dir
        self.index_table_name = index_table_name
        os.makedirs(self.block_dir, exist_ok=True)

    def build_index(self, table_name: str):
        self.doc_count = 0
        self._process_documents(table_name)
        full_index = self._external_merge_blocks_with_tfidf()
        self._save_index_to_table(full_index)
        self._clean_blocks()

    def _process_documents(self, table_name: str):
        heapfile: HeapFile = HeapFile(table_name)
        term_dict = defaultdict(lambda: defaultdict(int))  # term -> {doc_id: freq}
        block_number = 0

        for doc_id, text in heapfile.iterate_text_documents():
            self.doc_count += 1
            tokens = preprocess(text)
            for token in tokens:
                term_dict[token][doc_id] += 1

                if len(term_dict) >= MAX_TERMS_PER_BLOCK:
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
        Corregido: Manejo adecuado de iteradores y prevención de KeyError
        """
        block_paths = [os.path.join(self.block_dir, f) for f in os.listdir(self.block_dir) if f.endswith(".pkl")]
        block_iters = []
        current_terms = {}
        heap = []
        N = self.doc_count
        merged_index = {}

        # Inicializar iteradores de bloques
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
            
            # Recolectar todas las ocurrencias del término en todos los bloques
            combined_postings = defaultdict(int)
            blocks_to_advance = []

            # Buscar el término en todos los bloques activos
            for i in list(current_terms.keys()):
                term, postings = current_terms[i]
                if term == smallest_term:
                    for doc_id, freq in postings.items():
                        combined_postings[doc_id] += freq
                    blocks_to_advance.append(i)
                    del current_terms[i]  # Remover del diccionario actual

            # Calcular TF-IDF
            df_t = len(combined_postings)
            idf = math.log(N / df_t) if df_t and N > 0 else 0
            postings_tfidf = [
                (doc_id, round(freq * idf, 5)) 
                for doc_id, freq in combined_postings.items()
            ]
            merged_index[smallest_term] = postings_tfidf

            # Avanzar los bloques procesados
            for i in blocks_to_advance:
                try:
                    term, postings = next(block_iters[i])
                    heapq.heappush(heap, (term, i))
                    current_terms[i] = (term, postings)
                except StopIteration:
                    # Fin del iterador de este bloque
                    pass

        print(f"[SPIMI] Merge externo completado con {len(merged_index)} términos.")
        return merged_index

    def _save_index_to_table(self, inverted_index):
        """
        Guarda el índice invertido (con TF-IDF) en la tabla.
        """
        schema = [("term", "50s"), ("postings", "text")]
        HeapFile.build_file(self.index_table_name, schema, "term")
        heapfile = HeapFile(self.index_table_name)

        for term, postings in inverted_index.items():
            postings_serialized = json.dumps(postings)  # [(doc_id, tfidf), ...]
            record = Record(schema, [term, postings_serialized])
            heapfile.insert_record(record)

        ExtendibleHashIndex.build_index(
            self.index_table_name,
            lambda field_name: heapfile.extract_index(field_name),
            "term"
        )
        print(f"[SPIMI] Índice TF-IDF guardado en '{self.index_table_name}' con índice hash en 'term'.")

    def _clean_blocks(self):
        """
        Elimina todos los archivos de bloques temporales.
        """
        for fname in os.listdir(self.block_dir):
            os.remove(os.path.join(self.block_dir, fname))
        os.rmdir(self.block_dir)
        print("[SPIMI] Bloques temporales eliminados.")
