import os
import pickle
import math
from collections import defaultdict
import sys
import json
from typing import Dict, List, Tuple, DefaultDict, Any, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from .utils_spimi import preprocess
from storage.HeapFile import HeapFile
from .ExtendibleHashIndex import ExtendibleHashIndex
from storage.Record import Record

class SPIMIIndexer:
    def __init__(self, block_dir: str = "index_blocks", index_table_name: str = "inverted_index"):
        self.block_dir = block_dir
        self.index_table_name = index_table_name
        os.makedirs(self.block_dir, exist_ok=True)

    def build_index(self, table_name: str) -> None:
        self.doc_count = 0
        self._process_documents(table_name)
        full_index, document_norms = self._external_merge_blocks_with_tfidf()
        self._save_index_to_table(full_index, document_norms)
        self._clean_blocks()

    def _process_documents(self, table_name: str) -> None:
        heapfile: HeapFile = HeapFile(table_name)
        term_dict = defaultdict(lambda: defaultdict(int))
        block_number = 0
        memory_limit = 100 * 1024 * 1024  # 100 MB

        for doc_id, text in heapfile.iterate_text_documents():
            self.doc_count += 1
            tokens = preprocess(text)
            for token in tokens:
                term_dict[token][doc_id] += 1

                if sys.getsizeof(term_dict) >= memory_limit:
                    self._dump_block(term_dict, block_number)
                    block_number += 1
                    term_dict.clear()

        if term_dict:
            self._dump_block(term_dict, block_number)

    def _dump_block(self, term_dict: Dict[str, Dict[int, int]], block_number: int) -> None:
        path = os.path.join(self.block_dir, f"block_{block_number}.pkl")
        sorted_dict = dict(sorted(term_dict.items()))
        with open(path, "wb") as f:
            pickle.dump(sorted_dict, f)
        print(f"[SPIMI] Bloque {block_number} guardado con {len(sorted_dict)} términos.")

    def _external_merge_blocks_with_tfidf(self) -> Tuple[
        Dict[str, List[Tuple[int, float]]], 
        Dict[int, float]
    ]:
        block_paths = [os.path.join(self.block_dir, f) for f in os.listdir(self.block_dir) if f.endswith(".pkl")]
        N = self.doc_count
        document_norms = defaultdict(float)
        
        # Si no hay bloques, retornar vacío
        if not block_paths:
            return {}, {}
        
        # Función para convertir bloque a formato TF-IDF
        def convert_to_tfidf(block: Dict[str, Dict[int, int]]) -> Dict[str, List[Tuple[int, float]]]:
            tfidf_block = {}
            for term, freqs in block.items():
                df_t = len(freqs)
                idf = math.log(N / df_t) if df_t and N > 0 else 0
                postings = []
                
                for doc_id, freq in freqs.items():
                    tf = 1 + math.log(freq) if freq > 0 else 0
                    tfidf = round(tf * idf, 5)
                    postings.append((doc_id, tfidf))
                    document_norms[doc_id] += tfidf ** 2
                
                tfidf_block[term] = postings
            return tfidf_block

        # Convertir todos los bloques a TF-IDF
        tfidf_blocks = []
        for path in block_paths:
            with open(path, 'rb') as f:
                block = pickle.load(f)
                tfidf_blocks.append(convert_to_tfidf(block))
        
        # Fusionar bloques TF-IDF
        def merge_two_tfidf_blocks(block1, block2):
            merged = {}
            all_terms = set(block1.keys()) | set(block2.keys())
            
            for term in sorted(all_terms):
                # Combinar postings de ambos bloques
                combined = {}
                
                # Agregar postings del primer bloque
                if term in block1:
                    for doc_id, tfidf in block1[term]:
                        combined.setdefault(doc_id, 0)
                        combined[doc_id] += tfidf
                
                # Agregar postings del segundo bloque
                if term in block2:
                    for doc_id, tfidf in block2[term]:
                        combined.setdefault(doc_id, 0)
                        combined[doc_id] += tfidf
                
                # Crear lista de postings combinados
                merged[term] = [(doc_id, tfidf) for doc_id, tfidf in combined.items()]
            
            return merged

        # Fusionar bloques por pares
        while len(tfidf_blocks) > 1:
            new_blocks = []
            for i in range(0, len(tfidf_blocks), 2):
                block1 = tfidf_blocks[i]
                block2 = tfidf_blocks[i+1] if i+1 < len(tfidf_blocks) else {}
                merged_block = merge_two_tfidf_blocks(block1, block2)
                new_blocks.append(merged_block)
            tfidf_blocks = new_blocks

        # El bloque final es el resultado
        final_index = tfidf_blocks[0]
        
        # Calcular normas finales
        document_norms = {doc_id: math.sqrt(norm) for doc_id, norm in document_norms.items()}
        
        return final_index, document_norms

    def _save_index_to_table(
        self,
        inverted_index: Dict[str, List[Tuple[int, float]]],
        document_norms: Dict[int, float]
    ) -> None:
        # 1. Guardar índice invertido principal
        schema_idx = [("term", "50s"), ("postings", "text")]
        HeapFile.build_file(self.index_table_name, schema_idx, "term")
        heapfile_idx = HeapFile(self.index_table_name)

        for term, postings in inverted_index.items():
            # Convertir a formato JSON
            valid_postings = []
            for doc_id, tfidf in postings:
                valid_postings.append([int(doc_id), float(tfidf)])
            
            postings_json = json.dumps(valid_postings)
            record = Record(schema_idx, [str(term), postings_json])
            heapfile_idx.insert_record(record)

        # 2. Guardar normas de documentos
        schema_norms = [("doc_id", "i"), ("norm", "f")]
        norms_table_name = f"{self.index_table_name}_norms"
        HeapFile.build_file(norms_table_name, schema_norms, "doc_id")
        heapfile_norms = HeapFile(norms_table_name)

        for doc_id, norm in document_norms.items():
            record = Record(schema_norms, [int(doc_id), float(norm)])
            heapfile_norms.insert_record(record)
        
        # 3. Crear índices hash
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

    def _clean_blocks(self):
        if os.path.exists(self.block_dir):
            for fname in os.listdir(self.block_dir):
                os.remove(os.path.join(self.block_dir, fname))
            os.rmdir(self.block_dir)
            print("[SPIMI] Bloques temporales eliminados.")