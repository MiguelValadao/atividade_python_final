Desenvolver um Painel de Controle de Tarefas completo utilizando Flask, integrando os seguinte recursos? 
1. Gerenciamento de rotas e templates
2. Banco de dados SQLite
3. Autenticação de usuários
4. CRUD completo de tarefas
5. Integração com API externa
6. Interface moderna com Bootstrap e icones

1) Estrutura inicial
- Configure o ambiente Flask com uma aplicação modular (app.py, templates/, static/)
- Crie uma estrutura base com o template base.html contendo o menu e a área de conteúdo

2) Banco de dados 
- Crie duas tabelas: 
-> usuarios ( id, nome, email, senha)
-> tarefas (id, titulo, descricao, status, usuario_id)
- utilize SQLite 3 e crie funções auxiliares para conectar e consultar o banco.

3) Autenticação
- implemente páginas de login, registro e logout
- use hash de senha (como wekzeug.security)
- proteja as rotas internas com sessão (session do Flask)

4) Integração com API externa
- Na página /dashboard, exiba também uma frase motivacional diária consumida de uma API pública (por exemplo: https://api.adviceslip.com/advice)

5) CRUD de tarefas
- Crie as rotas: 
-> /dashboard - exibe todas as tarefas do usuário logado
-> /nova_tarefa - formulário de criação
-> /editar/<id> - edição de tarefa
-> /excluir/<id> - remoção da tarefa

6) Interface e estilo 
- Utilize Boostrap 5 para estilizar formulários, botoes e cards de tarefas. 
- Aplique ícones do Bootstrap para ações (editar, excluir, concluir)
- Mantenha a interface responsiva e agradável

7) Segurança e boas praticas 
- Configure SECRET_KEY no Flask
- Use DEBUG=False no ambiente de produção
- Oculte senhas e valide dados de entrada 

8) Filtro de tarefas por Status
Amplie o painel de controle para permitir que o usuário visualize apenas as tarefas pendentes, em andamento ou concluídas. Implemente um menu suspenso (dropdown) com as opções de filtro e exiba o resultado sem recarregar toda a página (usando uma rota que retorna JSON)

Desafio: altere as cores dos cards conforme os status: 
 - Pendente -> amarelo
 - Em andamento -> azul
 - Concluída -> verde 

9) Modo escuro e Personalização
Implemente um modo escuro no Painel de controle. Use classes do Boostrap (bg-dark, text-light) e salve a preferência do usuário em localStorage para que o modo escolhido persista ao recarregar a pagina 

10) Dashboard de Progresso
Crie uma pagina adicional /dashboard que mostre o progresso das tarefas de forma visual. Use greficos de barras ou pizza com Chart.js para representar a quantidade de tarefas por Status (pendente, em andamento e concluida). Os dados devem vir de uma rota Flask que retorna JSON.
