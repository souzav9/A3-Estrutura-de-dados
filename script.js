const API = "http://localhost:8000"; // backend python

document.getElementById("form-cadastro").addEventListener("submit", async (event) => {
    event.preventDefault();

    const cliente = {
        id: document.getElementById("id").value,
        nome: document.getElementById("nome").value,
        tipo: document.getElementById("tipo").value,
        tempo: Number(document.getElementById("tempo").value),
        chegada: document.getElementById("chegada").value,
    };

    const res = await fetch(API + "/cadastrar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cliente),
    });

    alert("Cliente cadastrado!");
});

document.getElementById("btn-processar").addEventListener("click", async () => {
    await fetch(API + "/processar");
    alert("Atendimento processado!");
});

document.getElementById("btn-estatisticas").addEventListener("click", async () => {
    const res = await fetch(API + "/estatisticas");
    const data = await res.json();
    document.getElementById("estatisticas").textContent = JSON.stringify(data, null, 2);
});
