// content.js - Extensão para o Projudi
// Integração: Cartório 6º BPM → PythonAnywhere
console.log("Extensão Integração Cartório 6 BPM Projudi iniciada!");

// -------------------------------------------------------
// Busca o valor de um campo pelo texto do seu label
// dentro de um container específico
// -------------------------------------------------------
function buscarValorPorLabel(container, textoLabel) {
    if (!container) return "";
    const labels = Array.from(container.querySelectorAll('.form_label, label, th, span, b, strong, td'));
    for (let label of labels) {
        const texto = label.innerText.trim().toUpperCase();
        if (texto.includes(textoLabel.toUpperCase())) {
            // Tenta pegar o próximo irmão direto
            let el = label.nextElementSibling;
            if (el && el.innerText.trim()) return el.innerText.trim();
            // Tenta o próximo irmão do pai
            el = label.parentElement ? label.parentElement.nextElementSibling : null;
            if (el && el.innerText.trim()) return el.innerText.trim();
        }
    }
    return "";
}

// -------------------------------------------------------
// Extração principal dos dados da página do Projudi
// -------------------------------------------------------
function extrairDadosProjudi() {
    let processo  = "";
    let noticiado = "";
    let substancia = "MACONHA";
    let quantidade = "0";
    let natureza   = "";

    // Container principal (#divDadosProcesso)
    const divProcesso = document.getElementById('divDadosProcesso');

    // ---- 1. NÚMERO DO PROCESSO ----
    if (divProcesso) {
        // Primeiro tenta pelo label "Número da Justiça" (informado pelo usuário)
        processo = buscarValorPorLabel(divProcesso, 'Número da Justiça');

        // Fallback: regex formato CNJ dentro do container
        if (!processo) {
            const match = divProcesso.innerText.match(/\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/);
            if (match) processo = match[0];
        }
    }
    // Fallback global: regex formato CNJ em toda a página
    if (!processo) {
        const match = document.body.innerText.match(/\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}/);
        if (match) processo = match[0];
    }

    // ---- 2. RÉU / NOTICIADO ----
    if (divProcesso) {
        noticiado = buscarValorPorLabel(divProcesso, 'Réu') ||
                    buscarValorPorLabel(divProcesso, 'Autuado') ||
                    buscarValorPorLabel(divProcesso, 'Parte');
    }
    if (!noticiado) {
        const labels = Array.from(document.querySelectorAll('.form_label, label, th, td, span'));
        for (let el of labels) {
            const t = el.innerText.trim().toUpperCase();
            if (t === 'RÉU:' || t === 'RÉU' || t.startsWith('NOTICIADO')) {
                const prox = el.nextElementSibling || el.parentElement?.nextElementSibling;
                if (prox && prox.innerText.trim()) { noticiado = prox.innerText.trim(); break; }
            }
        }
    }

    // ---- 3. NATUREZA / CLASSE ----
    if (divProcesso) {
        natureza = buscarValorPorLabel(divProcesso, 'Natureza') ||
                   buscarValorPorLabel(divProcesso, 'Classe') ||
                   buscarValorPorLabel(divProcesso, 'Crime');
    }

    // ---- 4. SUBSTÂNCIA (detecta pelo texto geral da página) ----
    const textoGeral = document.body.innerText.toUpperCase();
    if (textoGeral.includes('COCAÍNA') || textoGeral.includes('COCAINA')) substancia = 'COCAINA';
    if (textoGeral.includes('CRACK')) substancia = 'CRACK';
    if (textoGeral.includes('ANFETAMINA')) substancia = 'ANFETAMINA';
    if (textoGeral.includes('ECSTASY') || textoGeral.includes('MDMA')) substancia = 'ECSTASY';

    // ---- 5. QUANTIDADE/PESO ----
    const matchPeso = textoGeral.match(/(\d+[\.,]\d+)\s*(G|KG|GRAMAS?|QUILOS?)/i);
    if (matchPeso) quantidade = matchPeso[1].replace(',', '.');

    // ---- DIAGNÓSTICO (F12 → Console para depuração) ----
    console.log("=== PROJUDI EXTRACTOR ===");
    console.log("  Processo :", processo);
    console.log("  Noticiado:", noticiado);
    console.log("  Natureza :", natureza);
    console.log("  Substância:", substancia, "| Qtd:", quantidade);
    if (divProcesso) {
        console.log("  [divDadosProcesso] Conteúdo (400 chars):");
        console.log("  ", divProcesso.innerText.substring(0, 400));
    } else {
        console.warn("  #divDadosProcesso NÃO encontrado nesta página.");
    }

    return {
        processo:  processo || prompt("Número do Processo não encontrado automaticamente.\nDigite manualmente (ex: 0000000-00.0000.8.16.0000):"),
        noticiado: noticiado || "NÃO ENCONTRADO",
        substancia: substancia,
        quantidade: quantidade,
        natureza:  natureza || "A classificar"
    };
}

// -------------------------------------------------------
// Botão Flutuante
// -------------------------------------------------------
const btn = document.createElement('button');
btn.innerText = "Enviar para Estatística (6º BPM)";
btn.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 999999;
    padding: 14px 20px;
    background-color: #1a3a2a;
    color: #c5a059;
    border: 2px solid #c5a059;
    border-radius: 8px;
    font-family: Arial, sans-serif;
    font-weight: bold;
    font-size: 13px;
    cursor: pointer;
    box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    transition: transform 0.1s ease;
`;

btn.addEventListener('mouseover', () => btn.style.transform = 'scale(1.04)');
btn.addEventListener('mouseout',  () => btn.style.transform = 'scale(1)');

// -------------------------------------------------------
// Ação ao clicar
// -------------------------------------------------------
btn.addEventListener('click', async () => {
    btn.innerText = "Extraindo e Enviando...";
    btn.style.opacity = '0.7';

    const dados = extrairDadosProjudi();

    if (!dados.processo) {
        alert("Operação cancelada: Processo não identificado.");
        btn.innerText = "Enviar para Estatística (6º BPM)";
        btn.style.opacity = '1';
        return;
    }

    try {
        const response = await fetch('https://1cartorio6bpm.pythonanywhere.com/api/receber_projudi/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.mensagem);
            if (result.url) window.open(result.url, '_blank');
        } else {
            alert("Erro no Cartório 6 BPM: " + (result.erro || "Falha desconhecida."));
        }
    } catch (err) {
        console.error(err);
        alert("Erro de conexão com o servidor do Cartório. Verifique se está logado em:\nhttps://1cartorio6bpm.pythonanywhere.com");
    } finally {
        btn.innerText = "Enviar para Estatística (6º BPM)";
        btn.style.opacity = '1';
    }
});

document.body.appendChild(btn);
