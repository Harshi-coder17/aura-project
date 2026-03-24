import { useState } from "react";
import InputBox from "./components/InputBox";
import ResponseBox from "./components/ResponseBox";
import { sendMessage } from "./services/api";

function App() {
  const [response, setResponse] = useState(null);

  const handleSubmit = async (text) => {
    try {
      const data = await sendMessage(text);
      console.log("API Response:", data);
      setResponse(data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div>
      <InputBox onSubmit={handleSubmit} />
      <ResponseBox data={response} />
    </div>
  );
}

export default App;