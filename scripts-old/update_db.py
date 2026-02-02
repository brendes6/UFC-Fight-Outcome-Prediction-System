from google.cloud import firestore

db = firestore.Client(project="ufc-proj", database="ufcdb")
fighters_ref = db.collection("fighters")

for doc in fighters_ref.stream():
    data = doc.to_dict()

    fighter_tag = data.get("fighter_tag")
    if not fighter_tag:
        print(f"Skipping {doc.id}: no fighter_tag")
        continue

    old_id = doc.id
    new_id = fighter_tag

    # Already correct
    if old_id == new_id:
        continue

    new_doc_ref = fighters_ref.document(new_id)

    # Safety: don’t overwrite existing docs
    if new_doc_ref.get().exists:
        print(f"Conflict: {new_id} already exists, skipping {old_id}")
        continue

    # Write new doc
    new_doc_ref.set(data)

    # Delete old doc
    fighters_ref.document(old_id).delete()

    print(f"Migrated {old_id} → {new_id}")
