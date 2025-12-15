
#  CONTRACT RISK & COMPLIANCE ASSESSMENT SYSTEM
#    Using Groq + Llama 3 + LangChain to:
#    1. Extract important clauses from uploaded contracts (PDF/TXT)
#    2. Assess risk level for each clause (using LLM)
#    3. Check compliance against GDPR, HIPAA, Indian Contract Act
#    4. Allow Q&A over contracts using RAG (Retrieval Augmented Generation)

import os
import json
import re
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq


#  ENVIRONMENT SETUP
# Loads the Groq API key from .env file to authenticate Llama 3 model.
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("GROQ_API_KEY not found in .env file! Add it before running again.")
    raise SystemExit(1)
print("Groq API key loaded successfully.")


# CONFIGURATION
# Sets paths for contract documents and FAISS vector index.
DOCS_PATH = "./contracts"
INDEX_DIR = "faiss_index"
os.makedirs(INDEX_DIR, exist_ok=True)


#  DOCUMENT LOADING MODULE
# Loads all contract files (PDF or TXT) from the given folder.
# Adds filename as metadata for retrieval tracking.
def load_documents(folder_path):
    docs = []
    print(f"\nScanning folder: {folder_path}")

    if not os.path.isdir(folder_path):
        print(f"Folder not found: {folder_path}")
        return docs

    for fname in os.listdir(folder_path):
        full_path = os.path.join(folder_path, fname)
        if fname.lower().endswith(".pdf"):
            print(f"→ Loading PDF: {fname}")
            docs.extend(PyPDFLoader(full_path).load())
        elif fname.lower().endswith(".txt"):
            print(f"→ Loading Text: {fname}")
            docs.extend(TextLoader(full_path).load())

    print(f"Loaded {len(docs)} document(s).")
    for d in docs:
        d.metadata = {"source": os.path.basename(d.metadata.get('source', 'unknown') or fname)}
    return docs


# TEXT CHUNKING MODULE
# Splits the loaded contracts into smaller 1000-character chunks
# to enable better semantic search and LLM comprehension.
def chunk_documents(docs):
    print("\n Splitting documents into chunks...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"→ Created {len(chunks)} chunks.")
    return chunks


#  VECTOR STORE CREATION (FAISS)
# Converts contract chunks into vector embeddings for semantic search.
# FAISS enables similarity-based retrieval for RAG Q&A.
def get_vector_store(chunks, index_path=INDEX_DIR):
    print("\n Preparing FAISS vector store...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    print("→ Rebuilding FAISS index from documents...")
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(index_path)
    print(f" FAISS index saved to {index_path}")
    return vs

#  JSON CLEANING UTILITY
# Extracts only the valid JSON portion from LLM outputs (removes markdown).
# Ensures robust parsing even if LLM adds extra text around JSON.
def extract_json_block(text):
    brace = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if brace == 0:
                start = i
            brace += 1
        elif ch == "}":
            if brace > 0:
                brace -= 1
                if brace == 0 and start != -1:
                    return text[start:i + 1]
    t = re.sub(r"```(?:json)?", "", text).strip()
    return t


#  LLM CLAUSE EXTRACTION MODULE
# Uses Groq + Llama 3 to extract key contract clauses like:
# Termination, Payment Terms, Confidentiality, Liability, Governing Law, etc.
# Returns results in clean JSON format.
def extract_key_clauses(docs, llm):
    print("\n Extracting key clauses...")
    full_text = "\n".join([d.page_content for d in docs])
    prompt = f"""
You are a contract analysis assistant.
Extract the following clauses clearly and concisely from the text below:
- Termination Clause
- Payment Terms
- Confidentiality Clause
- Liability Clause
- Governing Law
- Dispute Resolution
- Duration / Validity
- Data Protection / Privacy
- Any other important clause (if present)
Return output strictly as RAW JSON only.

Contract text:
{full_text}
"""
    resp = llm.invoke(prompt)
    return resp.content


# LLM RISK ASSESSMENT MODULE
# Asks the LLM to assign risk levels (High/Medium/Low)
# to each extracted clause and explain reasoning briefly.
def assess_risks(clause_summary, llm):
    print("\n Performing LLM-based risk assessment...")
    prompt = f"""
You are a legal compliance assistant.
Analyze the following contract clauses and assign a risk level (High / Medium / Low).
Explain briefly why each was rated that way.
Return RAW JSON only.

Clauses:
{clause_summary}
"""
    resp = llm.invoke(prompt)
    return resp.content


#  RULE-BASED COMPLIANCE CHECK MODULE
# Adds custom logic to flag possible compliance violations based on:
# - GDPR (Data consent, retention, cross-border transfer)
# - Indian Contract Act (Termination notice, liability, dispute resolution)
def check_compliance(clauses):
    flags = {}
    for name, text in clauses.items():
        if isinstance(text, dict):
            text = " ".join(str(v) for v in text.values())
        if not isinstance(text, str):
            continue

        text_lower = text.lower()
        clause_flags = []

        # GDPR checks
        if "personal data" in text_lower and "consent" not in text_lower:
            clause_flags.append("GDPR: Missing user consent for data processing.")
        if "data retention" in text_lower and "duration" not in text_lower:
            clause_flags.append("GDPR: Retention duration not specified.")
        if "transfer" in text_lower and "outside" in text_lower and "protection" not in text_lower:
            clause_flags.append("GDPR: Cross-border data transfer missing protection clause.")

        # Indian Contract Act checks
        if "terminate" in text_lower and "notice" not in text_lower:
            clause_flags.append("Indian Contract Act: Missing notice period in termination clause.")
        if "liability" in text_lower and "unlimited" in text_lower:
            clause_flags.append("Indian Contract Act: Unlimited liability may be unenforceable.")
        if "dispute" in text_lower and "arbitration" not in text_lower and "court" not in text_lower:
            clause_flags.append("Indian Contract Act: Missing dispute resolution mechanism.")

        if clause_flags:
            flags[name] = clause_flags
    return flags



# HYBRID RISK + COMPLIANCE INTEGRATION
# Combines:
# - LLM risk output (qualitative)
# - Rule-based compliance checks (quantitative)
# to produce a unified final report.
def assess_risks_with_compliance(clauses_json, llm):
    print("\n Integrating rule-based compliance checks...")
    try:
        cleaned = extract_json_block(clauses_json)
        clauses = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(" Error: Clause extraction JSON invalid.", e)
        print(" Raw LLM output (first 600 chars):\n", clauses_json[:600])
        return {}

    base_assessment_raw = assess_risks(cleaned, llm)
    try:
        base_clean = extract_json_block(base_assessment_raw)
        base_json = json.loads(base_clean)
    except Exception as e:
        print(" Warning: LLM risk output not strict JSON. Skipping merge.", e)
        return base_assessment_raw

    compliance_flags = check_compliance(clauses)
    for clause, risk_data in base_json.items():
        if clause in compliance_flags:
            if isinstance(risk_data, dict):
                risk_data["compliance_flags"] = compliance_flags[clause]
            else:
                base_json[clause] = {
                    "assessment": risk_data,
                    "compliance_flags": compliance_flags[clause],
                }
    return base_json



# PARTY DETECTION MODULE
# Uses regex to find the contracting parties (e.g., "Between AlphaTech and BetaSoft")
# Useful for displaying which companies or individuals are involved.
def find_parties_from_raw(docs):
    text = "\n".join(d.page_content for d in docs)
    patterns = [
        r'between\s+(.+?)\s*\((?:\"|“)?(?:provider|first party)(?:\"|”)?\)\s*and\s+(.+?)\s*\((?:\"|“)?(?:client|second party)(?:\"|”)?\)',
        r'between\s+(.+?)\s+and\s+(.+?)\s*,?\s*(?:collectively|hereinafter)?',
        r'parties involved[^:]*:\s*(.+?)\s+and\s+(.+?)\b',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            p1 = re.sub(r'\s+', ' ', m.group(1)).strip(' "’“”')
            p2 = re.sub(r'\s+', ' ', m.group(2)).strip(' "’“”')
            return p1, p2
    return None


# RAG-BASED Q&A SYSTEM MODULE
# Allows interactive querying of the contract using semantic search.
# Automatically retrieves relevant text and uses the LLM to answer queries.
def create_rag_chain(vector_store, preferred_source="service_agreement.pdf"):
    print("\n Setting up RAG-based Q&A system...")
    retriever_pdf = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 3, "filter": {"source": preferred_source}}
    )
    retriever_all = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    assistant_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.2)

    def query_contract(question):
        try:
            docs_found = retriever_pdf.invoke(question)
        except Exception:
            docs_found = None

        if not docs_found:
            try:
                docs_found = retriever_all.invoke(question)
            except Exception:
                docs_found = None
            used = "ALL"
        else:
            used = preferred_source

        if not docs_found:
            return "No relevant info found in the document."

        print("\nRetrieved Context Preview (from:", used, ")")
        for d in docs_found:
            src = d.metadata.get("source", "Unknown")
            snippet = d.page_content[:220].replace("\n", " ")
            print(f"- {src}: {snippet} ...")
        print("----")

        if re.search(r'\bwho (are|is) the (parties|party)\b', question.lower()):
            parties = find_parties_from_raw(docs_found) or find_parties_from_raw(vs_docstore_docs(vector_store))
            if parties:
                return f"The contract is between {parties[0]} and {parties[1]}."

        context = "\n\n".join([doc.page_content for doc in docs_found])
        prompt = f"""
You are a legal assistant AI.
Answer strictly using the contract text below. If unsure, say 'not found in the contract'.

Contract text:
{context}

Question: {question}
Answer:
"""
        resp = assistant_llm.invoke(prompt)
        try:
            return resp.content.strip()
        except Exception:
            return str(resp).strip()

    return query_contract


# DOCSTORE HELPER
# Retrieves all stored documents from FAISS docstore
def vs_docstore_docs(vector_store):
    try:
        return [vector_store.docstore._dict[k] for k in vector_store.docstore._dict]
    except Exception:
        return []


#MAIN EXECUTION PIPELINE
#complete workflow:
# 1 Load → 2 Chunk → 3 Analyze → 4 Assess → 5 Save → 6 Q&A
def main():
    print("\nStarting Contract Risk Assessment System (Groq + Llama3 + Compliance + RAG)...")

    documents = load_documents(DOCS_PATH)
    if not documents:
        return

    chunks = chunk_documents(documents)

    llm_for_analysis = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.2)

    clauses_json = extract_key_clauses(documents, llm_for_analysis)
    print("\n Extracted Key Clauses:\n", clauses_json)

    final_report = assess_risks_with_compliance(clauses_json, llm_for_analysis)
    print("\n Final Risk & Compliance Assessment:\n",
          json.dumps(final_report, indent=2) if isinstance(final_report, dict) else final_report)

    try:
        with open("risk_assessment_output.json", "w") as f:
            if isinstance(final_report, dict):
                json.dump(final_report, f, indent=2)
            else:
                f.write(str(final_report))
        print("\n Results saved to risk_assessment_output.json")
    except Exception as e:
        print(" Could not write output file:", e)

    vs = get_vector_store(chunks, index_path=INDEX_DIR)
    chat = create_rag_chain(vs, preferred_source="service_agreement.pdf")

    print("\n Ask questions about the contract (type 'exit' to quit):")
    while True:
        try:
            q = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n Exiting (input interrupted).")
            break

        if q.lower() in {"exit", "quit", "q"}:
            print("Exiting.")
            break

        print("AI:", chat(q))


# PROGRAM ENTRY POINT
if __name__ == "__main__":
    main()
