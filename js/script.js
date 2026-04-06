const btn = document.querySelector("button");

btn.addEventListener("click", () => {
    alert("Que bom que esteja ajudando!");
});

let numero = 0;
const contador = document.getElementById("contador");

const intervalo = setInterval(() => {
    numero += 10;
    contador.innerText = numero;

    if (numero >= 2500) {
        clearInterval(intervalo);
    }
}, 40);

document.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", function(e) {
        const destino = this.getAttribute("href");

        if (destino.startsWith("#")) {
            e.preventDefault();
            document.querySelector(destino).scrollIntoView({
                behavior: "smooth"
            });
        }
    });
});

const imagens = [
    "/Ong-Connect/assets/Homeimg.webp",
    "/Ong-Connect/assets/grupo.luta.png",
    "/Ong-Connect/assets/casasantagemma.jpg",
    "/Ong-Connect/assets/Cachorro.webp"
];

let index = 0;
const img = document.querySelector("main img");

const barra = document.getElementById("barra");

let tempo = 0;
const duracao = 4000; 

function trocarImagem() {
    index = (index + 1) % imagens.length;
    img.src = imagens[index];
    tempo = 0;
    barra.style.width = "0%";
}

setInterval(() => {
    tempo += 50;

    let porcentagem = (tempo / duracao) * 100;
    barra.style.width = porcentagem + "%";

    if (tempo >= duracao) {
        trocarImagem();
    }
}, 50);

img.addEventListener("click", trocarImagem);

// const textoH1 = "Conectando quem quer ajudar com quem precisa";
// const textoH4 = "Encontre ONGs, se voluntarie e transforme vidas";

// const h1 = document.querySelector("h1");
// const h4 = document.querySelector("h4");

// let i = 0;
// let j = 0;

// h1.textContent = "";
// h4.textContent = "";

// function escreverH1() {
//     if (i < textoH1.length) {
//         h1.textContent += textoH1[i];
//         i++;
//         setTimeout(escreverH1, 50);
//     } else {
//         // quando terminar o h1, começa o h4
//         setTimeout(escreverH4, 300); // pequeno delay fica mais bonito
//     }
// }

// function escreverH4() {
//     if (j < textoH4.length) {
//         h4.textContent += textoH4[j];
//         j++;
//         setTimeout(escreverH4, 30);
//     }
// }

// escreverH1();