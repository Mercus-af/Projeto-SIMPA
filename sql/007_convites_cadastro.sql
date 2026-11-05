-- Código de uso único para vincular uma nova conta ao aluno autorizado.
CREATE TABLE IF NOT EXISTS simpa.convites_cadastro (
    aluno_id BIGINT PRIMARY KEY REFERENCES simpa.alunos(id) ON DELETE CASCADE,
    codigo_hash TEXT NOT NULL UNIQUE,
    criado_por BIGINT NOT NULL REFERENCES simpa.usuarios(id),
    expira_em TIMESTAMPTZ NOT NULL,
    utilizado_em TIMESTAMPTZ
);
