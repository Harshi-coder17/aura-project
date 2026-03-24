import { useState } from "react";

function InputBox({ onSubmit }) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    console.log("Button clicked"); // 👈 DEBUG
    if (!text.trim()) return;
    onSubmit(text);
    setText("");
  };

  return (
    <div style={styles.container}>
      <h2>AURA Assistant</h2>

      <textarea
        placeholder="Describe the emergency..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={styles.textarea}
      />

      <button onClick={handleSubmit} style={styles.button}>
        Submit
      </button>
    </div>
  );
}

const styles = {
  container: {
    textAlign: "center",
    marginTop: "50px",
  },
  textarea: {
    width: "60%",
    height: "120px",
    padding: "10px",
    fontSize: "16px",
    marginBottom: "10px",
  },
  button: {
    padding: "10px 20px",
    fontSize: "16px",
    cursor: "pointer",
  },
};

export default InputBox;