# Create a small script to auto-draft ground truth candidates, then have an admin/supervisor verify.
def generate_ground_truth_candidates(questions: List[str], batch_owner: str="auto"):
    for q in questions:
        prompt = f"Produce a concise, correct, academic-style answer for learners: {q}\nKeep it ~100-250 words."
        resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=[{"role":"user","content":prompt}], temperature=0.0)
        candidate = resp["choices"][0]["message"]["content"].strip()
        # Save to ground_truths (verified=false) for supervisor review
        insert_ground_truth(q, candidate, created_by=batch_owner)
