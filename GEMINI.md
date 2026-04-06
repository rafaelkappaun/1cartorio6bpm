📑 Guia de Desenvolvimento: Sistema de Gestão de Cartório (6º BPM)
🎯 Visão do Projeto
Este sistema é uma plataforma Fullstack (Django + React) para gestão completa de cartório policial. O objetivo é superar o controle de entorpecentes, permitindo a gestão de todos os tipos penais e todos os materiais apreendidos em Termos Circunstanciados (TC).

💎 Estética e UX (Frontend React)
Estilo: "Elegante & Minimalista".

Paleta de Cores: Fundo claro (#f8f9fa), elementos de destaque em Verde Militar PMPR (#1a3a2a) e detalhes em Dourado Sutil (#c5a059).

UX: Dashboard limpo, tipografia moderna (Inter ou Roboto), uso de ícones leves (Lucide-React) e transições suaves (Framer Motion).

🏗️ Estrutura de Dados (Backend Django)
O sistema deve ser capaz de diferenciar o fluxo de cada objeto baseado no seu destino final:

Entorpecentes: - Destino: Custódia no BPM.

Fluxo: Pesagem, lacração, armazenamento no cofre e posterior incineração.

Materiais Gerais (Celulares, Armas, Objetos):

Destino: Encaminhamento ao Fórum.

Fluxo: Cadastro, geração de Ofício de Remessa, transporte e upload do comprovante de recebimento (baixa).

Dinheiro/Valores:

Destino: Depósito Judicial.

Fluxo: Geração de guia de depósito e registro do comprovante bancário.

🚀 Comandos de Inicialização (Antigravity Terminal)
Gemini, por favor, execute ou verifique a instalação destas dependências para garantir o funcionamento fullstack:

Bash
# Backend - API e Documentos
pip install djangorestframework django-cors-headers reportlab python-docx drf-spectacular

# Frontend - UI e Gerenciamento de Estado
npm install lucide-react axios framer-motion @tanstack/react-table clsx tailwind-merge
📄 Regras de Negócio para Documentos (Automação)
O sistema deve gerar automaticamente um Ofício em PDF:

Conteúdo: Cabeçalho oficial do 6º BPM, dados do BOU, relação detalhada dos itens destinados ao Fórum.

Protocolo: O sistema deve prever um campo para "Upload de Recibo" para que o escrivão anexe a via assinada pelo Fórum, alterando o status do item para "Entregue ao Judiciário".

🛠️ Instruções para a IA (Gemini)
Ao me ajudar a codificar:

Priorize Django Rest Framework (DRF) para as APIs.

No React, utilize Tailwind CSS para manter o design minimalista.

Sempre que criar um modelo, inclua campos de auditoria (criado_por, data_criacao, ultima_alteracao).

Garanta que a lógica de "Ofício de Material Apreendido" agrupe vários itens de um mesmo BOU em um único documento.