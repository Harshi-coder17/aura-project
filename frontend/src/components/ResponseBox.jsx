function ResponseBox({ data }) {
  if (!data) return null;

  return (
    <div style={{ marginTop: "20px" }}>
      <h3>FULL RESPONSE:</h3>

      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

export default ResponseBox;