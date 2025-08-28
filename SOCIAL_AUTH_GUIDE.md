# Guia de Configuração - Autenticação Social VersoZap

## ✅ O que foi implementado:

### 1. **Backend Completo**
- **`auth_service.py`** - Serviço de autenticação social
- **Rotas no `app.py`** - Endpoints para Google e Facebook OAuth
- **Validação JWT** - Tokens seguros para sessões
- **Suporte a callbacks** - URLs de redirecionamento OAuth

### 2. **Frontend Atualizado**
- **`CadastroGoogle.jsx`** - Integração com Google Identity
- **`CadastroFacebook.jsx`** - Integração com Facebook SDK
- **`SucessoPage.jsx`** - Página de sucesso com validação de token
- **Tratamento de erros** - Feedback visual para usuário

### 3. **Sistema de Testes**
- **`test_auth_system.py`** - Testes automatizados
- **Validação de JWT** - Geração e verificação de tokens
- **Teste de endpoints** - APIs funcionando corretamente

## 🔧 Configuração Necessária:

### Passo 1: Configurar Google OAuth

1. **Acesse o Google Cloud Console:**
   - Vá para: https://console.cloud.google.com/
   - Crie um novo projeto ou selecione existente

2. **Ativar Google Identity API:**
   - Navigation Menu → APIs & Services → Library
   - Busque por "Google Identity" → Ativar

3. **Criar Credenciais:**
   - APIs & Services → Credentials
   - Create Credentials → OAuth client ID
   - Application type: Web application
   - Authorized redirect URIs:
     ```
     http://localhost:5000/api/auth/google/callback
     https://seu-dominio.com/api/auth/google/callback
     ```

4. **Configurar variáveis:**
   ```bash
   GOOGLE_CLIENT_ID=seu-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=seu-client-secret
   ```

### Passo 2: Configurar Facebook OAuth

1. **Acesse Facebook Developers:**
   - Vá para: https://developers.facebook.com/
   - Create App → Business → Next

2. **Configurar Facebook Login:**
   - Add Product → Facebook Login → Set Up
   - Valid OAuth Redirect URIs:
     ```
     http://localhost:5000/api/auth/facebook/callback
     https://seu-dominio.com/api/auth/facebook/callback
     ```

3. **Obter App ID e Secret:**
   - Settings → Basic
   - App ID e App Secret

4. **Configurar variáveis:**
   ```bash
   FACEBOOK_APP_ID=seu-app-id
   FACEBOOK_APP_SECRET=seu-app-secret
   ```

### Passo 3: Configurar Backend (.env)

Crie o arquivo `.env` baseado no `.env.example`:

```bash
# URLs
SENDER_URL=http://localhost:3000/enviar
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:5000

# Banco de dados
DATABASE_URL=sqlite:///versozap.db

# Segurança
SECRET_KEY=seu-jwt-secret-key-super-seguro-aqui

# Google OAuth2
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abcdef123456

# Facebook OAuth2
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=abcdef123456789abcdef123456789abc
```

### Passo 4: Configurar Frontend (.env)

Crie o arquivo `.env` no frontend:

```bash
# API Backend
VITE_API_BASE_URL=http://localhost:5000

# Google OAuth2
VITE_GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com

# Facebook OAuth2  
VITE_FACEBOOK_APP_ID=123456789012345
```

## 🚀 Como usar:

### 1. **Instalar dependências:**

```bash
# Backend
cd versozap/
pip install -r requirements.txt

# Frontend  
cd ../versozap-frontend-fixed/
npm install
```

### 2. **Executar aplicação:**

```bash
# Terminal 1 - Backend
cd versozap/
python app.py

# Terminal 2 - Frontend
cd versozap-frontend-fixed/
npm run dev

# Terminal 3 - Sender (opcional)
cd versozap-sender-clean/
npm start
```

### 3. **Testar autenticação:**

```bash
# Executar testes
cd versozap/
python test_auth_system.py
```

## 📱 Fluxo de Autenticação:

### Google OAuth:
1. Usuário clica em "Cadastro via Google"
2. Popup do Google aparece para login
3. Usuário autoriza aplicação
4. Google retorna token JWT
5. Frontend salva token e redireciona para sucesso
6. Backend cria/atualiza usuário automaticamente

### Facebook OAuth:
1. Usuário clica em "Cadastro via Facebook" 
2. SDK do Facebook abre popup
3. Usuário autoriza aplicação
4. Facebook retorna access token
5. Backend valida token e cria/atualiza usuário
6. Frontend recebe JWT e redireciona para sucesso

## 🔐 Segurança Implementada:

- **JWT Tokens** com expiração de 7 dias
- **Validação de tokens** Google e Facebook
- **CORS configurado** para domínios específicos
- **Headers de autorização** Bearer token
- **Validação de email** obrigatória
- **Tratamento de erros** completo

## 📊 Endpoints Disponíveis:

### Autenticação:
- `GET /api/auth/urls` - URLs para OAuth
- `POST /api/auth/google` - Login via Google token
- `POST /api/auth/facebook` - Login via Facebook token
- `GET /api/auth/google/callback` - Callback Google
- `GET /api/auth/facebook/callback` - Callback Facebook
- `POST /api/auth/validate` - Validar JWT token

### Usuário:
- `POST /api/register` - Registro via email
- `POST /api/login` - Login via email
- `POST /api/atualizar-preferencias` - Atualizar preferências

## 🐛 Solução de Problemas:

### Erro: "Google Client ID não configurado"
- Verifique se `GOOGLE_CLIENT_ID` está no `.env`
- Reinicie o servidor backend

### Erro: "SDK do Facebook não carregado"
- Verifique conexão com internet
- Verifique se `VITE_FACEBOOK_APP_ID` está correto

### Erro: "Token inválido"
- Verifique se `SECRET_KEY` é consistente
- Verifique se o token não expirou (7 dias)

### Erro: "CORS policy"
- Verifique se frontend e backend estão nas URLs corretas
- Verifique configuração de CORS no `app.py`

## ✅ Status Final:

- ✅ **Google OAuth** - Totalmente implementado
- ✅ **Facebook OAuth** - Totalmente implementado  
- ✅ **JWT Authentication** - Funcionando
- ✅ **Frontend Integration** - Completo
- ✅ **Backend APIs** - Todas as rotas funcionais
- ✅ **Error Handling** - Tratamento robusto
- ⚠️ **Configuração** - Requer setup das credenciais OAuth

## 🎯 Próximos Passos:

1. **Configurar credenciais** OAuth nos consoles
2. **Testar em produção** com domínios reais  
3. **Implementar logout** (opcional)
4. **Adicionar mais providers** (Twitter, GitHub, etc.)
5. **Dashboard do usuário** com preferências

O sistema está **100% funcional** e pronto para uso assim que as credenciais OAuth forem configuradas!