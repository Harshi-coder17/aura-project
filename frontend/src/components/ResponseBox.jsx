// frontend/src/components/ResponseBox.jsx
// Lightweight debug/display component — kept but not used in main flow
export default function ResponseBox({ data }) {
  if (!data) return null;
  return (
    <div className="mt-4 p-4 bg-gray-100 rounded-xl text-left text-sm
                    font-mono whitespace-pre-wrap break-words">
      {JSON.stringify(data, null, 2)}
    </div>
  );
}