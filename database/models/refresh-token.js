const { Schema, model } = require("mongoose");

const RTSchema = Schema({
  user: {
    type: Schema.Types.ObjectId,
    ref: "user",
  },
  token: {
    type: String,
    index: true,
  },
  expire_at: {
    type: Date,
    // Each login creates its own token; MongoDB deletes expired ones automatically (TTL index).
    expires: 0,
  },
  researcher: {
    type: Schema.Types.ObjectId,
    ref: "researcher",
  },
  student: {
    type: Schema.Types.ObjectId,
    ref: "student",
  },
});

const RTModel = model("refresh_token", RTSchema);

module.exports = RTModel;
