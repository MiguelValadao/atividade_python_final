document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("btnDark");
    if (!btn) {
        return;
    }

    var icone = btn.querySelector("i");

    function aplicar(escuro) {
        document.documentElement.setAttribute("data-bs-theme", escuro ? "dark" : "light");
        document.body.classList.toggle("bg-dark", escuro);
        document.body.classList.toggle("text-light", escuro);
        icone.className = escuro ? "bi bi-sun" : "bi bi-moon-stars";
        localStorage.setItem("modoEscuro", escuro ? "1" : "0");
    }

    aplicar(localStorage.getItem("modoEscuro") === "1");

    btn.addEventListener("click", function () {
        var escuro = document.documentElement.getAttribute("data-bs-theme") === "dark";
        aplicar(!escuro);
    });
});