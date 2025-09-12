from typing import Dict, Any, List

GENERAL_DISCLAIMER = (
    "Saya AGI prososial. Informasi bersifat umum, bukan pengganti profesional. "
    "Utamakan keselamatan, privasi, hukum setempat, dan nilai kemanusiaan."
)

MEDICAL_DISCLAIMER = (
    "Bukan pengganti tenaga medis. Untuk darurat hubungi layanan darurat/IGD. "
    "Tidak memberi diagnosis, resep, atau dosis obat."
)

LEGAL_DISCLAIMER = (
    "Bukan nasihat hukum. Konsultasikan kasus spesifik ke penasihat hukum berizin di yurisdiksi Anda."
)

FINANCE_DISCLAIMER = (
    "Bukan saran investasi. Nilai dapat turun/naik. Lakukan riset mandiri dan pahami risiko."
)

class DomainAdapter:
    name: str = "base"
    def supports(self, prompt: str, meta: Dict[str,Any]) -> bool: return True
    def precheck(self, prompt: str, meta: Dict[str,Any]) -> Dict[str,Any]:
        return {"disclaimer": GENERAL_DISCLAIMER}
    def reshape_plan(self, steps: List[Dict[str,Any]], meta: Dict[str,Any]) -> List[Dict[str,Any]]:
        # filter PII & tindakan berisiko umum
        def bad(x):
            c=(x.get("cmd","") or "").lower()
            return any(k in c for k in ["collect pii","share personal","track user","exploit","phishing"])
        return [s for s in steps if not bad(s)]
    def risk_report(self, steps: List[Dict[str,Any]], meta: Dict[str,Any]) -> Dict[str,Any]:
        return {"risk":"low"}

class MedicalAdapter(DomainAdapter):
    name="medical"
    def supports(self,prompt,meta): 
        return any(k in prompt.lower() for k in ["diagnose","gejala","symptom","drug","therapy","bpjs","klinik","dokter"])
    def precheck(self,prompt,meta):
        return {"disclaimer":"Bukan pengganti tenaga medis; hubungi profesional; darurat → IGD."}
    def reshape_plan(self,steps,meta):
        out=[]
        for s in steps:
            c=(s.get("cmd","") or "").lower()
            if any(k in c for k in ["diagnose","resep","dose","dosis","tindakan klinis","anjuran obat"]):
                continue  # block tindakan medis langsung
            out.append(s)
        return out
    def risk_report(self,steps,meta): return {"risk":"medium","notes":"Medical domain—restrict direct treatment actions."}

class LegalAdapter(DomainAdapter):
    name="legal"
    def supports(self,prompt,meta):
        return any(k in prompt.lower() for k in ["contract","perjanjian","uu","pasal","gugatan","legal"])
    def precheck(self,prompt,meta):
        return {"disclaimer":"Informasi umum, bukan nasihat hukum. Konsultasikan ke penasihat hukum berizin."}
    def reshape_plan(self,steps,meta): return steps
    def risk_report(self,steps,meta): return {"risk":"medium"}

class FinanceAdapter(DomainAdapter):
    name="finance"
    def supports(self,prompt,meta):
        return any(k in prompt.lower() for k in ["saham","invest","obligasi","pajak","cash flow","arus kas","npv","roi"])
    def precheck(self,prompt,meta):
        return {"disclaimer":"Bukan saran investasi. Risiko ditanggung pengguna."}
    def reshape_plan(self,steps,meta): return steps
    def risk_report(self,steps,meta): return {"risk":"medium"}

class GovernanceAdapter(DomainAdapter):
    name="governance"
    def supports(self,prompt,meta):
        return any(k in prompt.lower() for k in ["kebijakan","policy","sop","audit","governance","compliance"])
    def precheck(self,prompt,meta): return {"disclaimer":"Mode governance ketat diaktifkan."}

class PrivacySafetyAdapter(DomainAdapter):
    name="privacy_safety"
    def supports(self,prompt,meta): return True
    def reshape_plan(self, steps, meta):
        """Remove steps that collect or spread personally identifiable information."""
        def bad(x: Dict[str, Any]) -> bool:
            c = (x.get("cmd", "") or "").lower()
            return any(
                k in c
                for k in [
                    "collect pii",
                    "upload contacts",
                    "share personal",
                    "face recognition bulk",
                    "track user",
                    "re-identification",
                    "deanonymize",
                ]
            )
        return [s for s in steps if not bad(s)]

REGISTRY=[MedicalAdapter(), LegalAdapter(), FinanceAdapter(), GovernanceAdapter(), PrivacySafetyAdapter()]
