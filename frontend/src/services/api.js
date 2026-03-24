export async function sendMessage(text) {
  try {
    const response = await fetch("/api/v1/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        session_id: "123",
        text: text,
        mode: "stranger",
        location: { lat: 0, lon: 0 }
      }),
    });

    const data = await response.json();
    return data;

  } catch (error) {
    console.error("API ERROR:", error);
    return null;
  }
}