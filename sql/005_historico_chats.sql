-- Histórico privado por conta e perfil. Não altera dados acadêmicos.
CREATE TABLE IF NOT EXISTS simpa.chats_assistente (
    id UUID PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES simpa.usuarios(id) ON DELETE CASCADE,
    perfil TEXT NOT NULL CHECK (perfil IN ('professor','aluno')),
    aluno_id BIGINT,
    titulo TEXT NOT NULL DEFAULT 'Novo chat' CHECK (length(titulo) BETWEEN 1 AND 80),
    filtros JSONB NOT NULL DEFAULT '{}'::jsonb,
    selecao JSONB NOT NULL DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_chats_assistente_usuario ON simpa.chats_assistente(usuario_id, atualizado_em DESC);
CREATE TABLE IF NOT EXISTS simpa.mensagens_assistente (
    id BIGSERIAL PRIMARY KEY,
    chat_id UUID NOT NULL REFERENCES simpa.chats_assistente(id) ON DELETE CASCADE,
    papel TEXT NOT NULL CHECK (papel IN ('user','assistant')),
    texto TEXT NOT NULL CHECK (length(texto) BETWEEN 1 AND 16000),
    fontes JSONB NOT NULL DEFAULT '[]'::jsonb,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mensagens_assistente_chat ON simpa.mensagens_assistente(chat_id,id);
