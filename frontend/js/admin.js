document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('lu_token');
    if (!token) window.location.href = 'login.html';

    const ingestBtn = document.getElementById('ingest-btn');
    const rawContent = document.getElementById('raw-content');
    const statusDiv = document.getElementById('status');
    const logoutBtn = document.getElementById('logout-btn');

    ingestBtn.addEventListener('click', async () => {
        const content = rawContent.value;
        if (!content) return alert("Please provide content");

        statusDiv.textContent = "Processing & Embedding... Please wait.";
        statusDiv.style.color = "var(--primary-light)";

        try {
            const response = await fetch('http://localhost:8000/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ content: content })
            });

            if (response.ok) {
                const data = await response.json();
                statusDiv.textContent = `✅ Successfully ingested chunks!`;
                statusDiv.style.color = "#4ade80";
                rawContent.value = "";
            } else {
                throw new Error("Ingestion failed");
            }
        } catch (err) {
            statusDiv.textContent = "❌ Error during ingestion. Check backend console.";
            statusDiv.style.color = "#f87171";
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('lu_token');
        window.location.href = 'index.html';
    });
});
