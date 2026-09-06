db = db.getSiblingDB("assistant");

db.createCollection("assistant_contexts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user_id", "schema_version", "context", "updated_at"],
      properties: {
        user_id: { bsonType: ["string", "objectId"] },
        schema_version: { bsonType: "int", minimum: 1 },
        context: { bsonType: "object" },
        updated_at: { bsonType: "date" },
      },
    },
  },
  validationLevel: "strict",
  validationAction: "error",
});

db.assistant_contexts.createIndex({ user_id: 1 }, { unique: true });
db.assistant_contexts.createIndex({ updated_at: -1 });

db.assistant_contexts.updateOne(
  { user_id: "demo-user" },
  {
    $setOnInsert: {
      schema_version: NumberInt(1),
      context: {
        person: {
          first_name: "Diego",
          locale: "es-GT",
          timezone: "America/Guatemala",
        },
        preferences: { topics: ["tecnología", "economía"], language: "es" },
        saved_items: [],
      },
      updated_at: new Date(),
    },
  },
  { upsert: true },
);
