const btnMenu = document.querySelector(".menuh");
const menu = document.querySelector(".menu-mobile");

btnMenu.addEventListener("click", (e) => {
  menu.classList.toggle("ativo");
  document.body.classList.toggle("no-scroll");

  e.stopPropagation(); // evita conflito com o clique fora
});

// clique fora
document.addEventListener("click", (e) => {
  const clicouDentroMenu = menu.contains(e.target);
  const clicouNoBotao = btn.contains(e.target);

  if (!clicouDentroMenu && !clicouNoBotao) {
    menu.classList.remove("ativo");
    document.body.classList.remove("no-scroll");
  }
});