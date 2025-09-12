from javu_agi.llm import call_llm

print("[reason] ->", call_llm("Sebutkan 3 perbedaan relativitas umum vs mekanika kuantum.", task_type="reason")[:120])
print("[code]   ->", call_llm("Tulis HTML 1 file yang menampilkan teks 'Hello AGI' di tengah.", task_type="code")[:120])
print("[web]    ->", call_llm("Ringkas alasan eksplorasi ruang penting (2 kalimat).", task_type="web")[:120])
print("[fast]   ->", call_llm("balas: ok", task_type="fast", max_tokens=8)[:120])
