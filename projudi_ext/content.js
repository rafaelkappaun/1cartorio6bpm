// content.js - Extensão para o Projudi
console.log("Extensão Integração Cartório 6 BPM Projudi iniciada!");

// Função para tentar extrair os dados da página
function extrairDadosProjudi() {
    // Como não temos o HTML exato do Projudi, construímos uma extração baseada em seletores típicos,
    // ou buscando as labels no texto da página para encontrar o valor ao lado.
    
    let processo = "";
    let noticiado = "";
    let substancia = "MACONHA"; // Default fallback
    let quantidade = "0";

    // Exemplo de busca de Processo por regex no texto da página
    const matchProcesso = document.body.innerText.match(/\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/);
    if (matchProcesso) {
        processo = matchProcesso[0];
    } else {
        // Fallback de seletor ID genérico
        const elProcesso = document.querySelector('#numeroProcesso') || document.querySelector('.numero-processo');
        if(elProcesso) processo = elProcesso.innerText.trim();
    }

    // Exemplo de busca para 'Réu', 'Noticiado' ou 'Indiciado'
    // Aqui usamos um seletor XPath simples (como aproximação) ou percorremos elementos
    const labels = Array.from(document.querySelectorAll('label, th, span, td, strong, b'));
    for (let el of labels) {
        let texto = el.innerText.toUpperCase();
        if (texto.includes('RÉU:') || texto.includes('RÉU :') || texto.includes('NOTICIADO:')) {
            let valorEl = el.nextElementSibling || el.parentElement.nextElementSibling;
            if (valorEl) {
                noticiado = valorEl.innerText.trim();
                break;
            }
        }
    }

    // Aproximação para buscar natureza / drogas em relatórios
    if (document.body.innerText.toUpperCase().includes('COCAÍNA')) substancia = 'COCAINA';
    if (document.body.innerText.toUpperCase().includes('CRACK')) substancia = 'CRACK';

    // Capturando quantidade (Ex: 0,550 g) - Regex genérica perto da palavra droga ou peso
    const matchPeso = document.body.innerText.match(/(\d+[\.\,]\d+)\s*(g|gramas|kg|quilos)/i);
    if (matchPeso) {
        quantidade = matchPeso[1];
    }

    return {
        processo: processo || prompt("Número do Processo (Projudi) não encontrado. Digite manualmente:"),
        noticiado: noticiado || "NOME NÃO ENCONTRADO",
        substancia: substancia,
        quantidade: quantidade,
        natureza: "Art. 28 - Uso de Entorpecentes" // Exemplo padrão
    };
}

// Criação do Botão Flutuante
const btn = document.createElement('button');
btn.innerText = "Enviar para Estatística (6º BPM)";
btn.style.position = 'fixed';
btn.style.bottom = '20px';
btn.style.right = '20px';
btn.style.zIndex = '999999';
btn.style.padding = '15px 20px';
btn.style.backgroundColor = '#1a3a2a'; // Verde PMPR
btn.style.color = '#c5a059'; // Dourado
btn.style.border = '2px solid #c5a059';
btn.style.borderRadius = '8px';
btn.style.fontFamily = 'Arial, sans-serif';
btn.style.fontWeight = 'bold';
btn.style.cursor = 'pointer';
btn.style.boxShadow = '0 4px 6px rgba(0,0,0,0.3)';

btn.addEventListener('mouseover', () => btn.style.transform = 'scale(1.05)');
btn.addEventListener('mouseout', () => btn.style.transform = 'scale(1)');

// Ação do Botão
btn.addEventListener('click', async () => {
    btn.innerText = "Extraindo e Enviando...";
    btn.style.opacity = '0.8';

    const dados = extrairDadosProjudi();

    if (!dados.processo) {
        alert("Operação cancelada: Processo não identificado.");
        btn.innerText = "Enviar para Estatística (6º BPM)";
        btn.style.opacity = '1';
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/receber_projudi/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.mensagem);
            if (result.url) {
                // Abre o sistema do cartório em uma nova aba para o Policial conferir e editar
                window.open(result.url, '_blank');
            }
        } else {
            alert("Erro no Cartório 6 BPM: " + (result.erro || "Falha desconhecida."));
        }
    } catch (err) {
        console.error(err);
        alert("Erro de conexão. O servidor do Django (Cartório) está rodando no 127.0.0.1:8000?");
    } finally {
        btn.innerText = "Enviar para Estatística (6º BPM)";
        btn.style.opacity = '1';
    }
});

// Adiciona o botão ao DOM
document.body.appendChild(btn);
