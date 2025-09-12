from javu_agi.rag.auto_ingest import auto_ingest
import sys
if __name__ == "__main__":
    folder = sys.argv[1] if len(sys.argv)>1 else "data/corpus"
    n = auto_ingest(folder)
    print("ingested:", n)
