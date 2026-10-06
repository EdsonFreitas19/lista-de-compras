# Lista de Desejos

Aplicativo web para organizar uma lista de desejos/compras. Você cadastra itens por um formulário (com imagem opcional), visualiza tudo em uma página principal e mantém a lista sempre à mão no navegador.

Feito com **Python + Flask**, banco **SQLite** e HTML/CSS simples.

## Funcionalidades

- Cadastro de itens por formulário
- Upload de imagem para cada item
- Listagem dos itens na página inicial
- Dados salvos localmente em um banco SQLite

## Tecnologias

- Python 3.10+
- Flask
- SQLite
- HTML e CSS (templates Jinja)

## Estrutura do projeto

```
lista-de-compras/
├── app.py               # aplicação Flask (rotas e banco)
├── requirements.txt     # dependências
├── static/
│   ├── style.css        # estilos
│   └── uploads/         # imagens enviadas (começa vazia)
└── templates/
    ├── base.html        # layout base
    ├── index.html       # página principal
    └── form.html        # formulário de cadastro
```

## Como rodar

### 1. Pré-requisitos

- [Python 3.10 ou superior](https://www.python.org/downloads/). No Windows, marque a opção **"Add python.exe to PATH"** durante a instalação.
- [Git](https://git-scm.com/) (opcional: dá para baixar o ZIP pelo botão **Code → Download ZIP** no GitHub).

Confira no terminal:

```
python --version
git --version
```

No Windows, se `python` não for reconhecido, use `py` no lugar.

### 2. Baixe o projeto

```
git clone https://github.com/EdsonFreitas19/lista-de-compras.git
cd lista-de-compras
```

### 3. Crie o ambiente virtual e instale as dependências

**Windows (CMD):**

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Linux / macOS:**

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Com o ambiente ativo, o terminal passa a mostrar `(venv)` no início da linha.

### 4. Rode o app

```
python app.py
```

Abra no navegador o endereço que aparecer no terminal, normalmente:

**http://127.0.0.1:5000**

Para parar o servidor, use `Ctrl + C`.

### Próximas vezes

Não precisa repetir tudo. Só entre na pasta, ative o ambiente e rode:

```
cd lista-de-compras
venv\Scripts\activate
python app.py
```

## Sobre o banco de dados

O arquivo do banco (`lista.db`) **não faz parte do repositório**, por isso a lista começa vazia em cada instalação. Os dados ficam salvos apenas no computador onde o app roda.

## Problemas comuns

- **`pip` ou `python` não reconhecido:** reinstale o Python marcando "Add python.exe to PATH", ou use `py -m pip` e `py`.
- **Porta em uso:** feche outra instância do app que esteja rodando.
- **Erro ao instalar dependências:** confirme que o ambiente virtual está ativo (`(venv)` no terminal).

## Autor

Gustavo — estudante de Sistemas de Informação na UPE.
