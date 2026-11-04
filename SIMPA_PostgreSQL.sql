-- SIMPA - Estrutura do banco PostgreSQL
-- Fonte: SIMPA_Marco_2.pdf (requisitos e regras de negocio).
-- Execute este arquivo uma unica vez em um banco simpa vazio.
-- Antes, conectado a postgres, execute separadamente:
-- CREATE DATABASE simpa WITH ENCODING = 'UTF8' TEMPLATE = template0;
-- Depois conecte-se a simpa e execute todo o restante deste arquivo.

BEGIN;
CREATE SCHEMA simpa;

-- 1. Usuarios: preparacao da persistencia para o login.
CREATE TABLE simpa.usuarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome VARCHAR(150) NOT NULL CHECK (btrim(nome) <> ''),
    matricula VARCHAR(30) UNIQUE,
    email_institucional VARCHAR(254),
    senha_hash TEXT NOT NULL CHECK (btrim(senha_hash) <> ''),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_usuario_matricula CHECK (
        matricula IS NULL OR
        (matricula = btrim(matricula) AND matricula <> '')
    ),
    CONSTRAINT ck_usuario_email CHECK (
        email_institucional IS NULL OR
        (email_institucional = btrim(email_institucional)
         AND email_institucional <> '')
    ),
    CONSTRAINT ck_usuario_identificador CHECK (
        matricula IS NOT NULL OR email_institucional IS NOT NULL
    )
);
CREATE UNIQUE INDEX uq_usuarios_email
    ON simpa.usuarios (lower(email_institucional));

-- 2. Turmas: contexto academico = ano letivo e semestre.
CREATE TABLE simpa.turmas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    identificador VARCHAR(50) NOT NULL,
    nome VARCHAR(150) NOT NULL CHECK (btrim(nome) <> ''),
    ano_letivo SMALLINT NOT NULL CHECK (ano_letivo > 0),
    semestre SMALLINT NOT NULL CHECK (semestre IN (1, 2)),
    situacao VARCHAR(15) NOT NULL DEFAULT 'ativa'
        CHECK (situacao IN ('ativa', 'inativa', 'concluida')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_turma_identificador CHECK (
        identificador = btrim(identificador)
        AND identificador <> ''
    ),
    CONSTRAINT uq_turma_contexto
        UNIQUE (identificador, ano_letivo, semestre)
);

-- 3. Alunos: uma unica ficha por matricula.
CREATE TABLE simpa.alunos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    matricula VARCHAR(30) NOT NULL UNIQUE,
    nome_completo VARCHAR(150) NOT NULL
        CHECK (btrim(nome_completo) <> ''),
    email_institucional VARCHAR(254),
    situacao_academica VARCHAR(15) NOT NULL DEFAULT 'ativo'
        CHECK (situacao_academica IN
            ('ativo', 'inativo', 'trancado', 'concluido')),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_aluno_matricula CHECK (
        matricula = btrim(matricula) AND matricula <> ''
    ),
    CONSTRAINT ck_aluno_email CHECK (
        email_institucional IS NULL OR
        (email_institucional = btrim(email_institucional)
         AND email_institucional <> '')
    )
);

-- 4. Disciplinas: catalogo de disciplinas do sistema.
CREATE TABLE simpa.disciplinas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    nome VARCHAR(150) NOT NULL CHECK (btrim(nome) <> ''),
    situacao VARCHAR(10) NOT NULL DEFAULT 'ativa'
        CHECK (situacao IN ('ativa', 'inativa')),
    CONSTRAINT ck_disciplina_codigo CHECK (
        codigo = btrim(codigo) AND codigo <> ''
    )
);

-- 5. Matriculas: vinculo do aluno com uma turma.
CREATE TABLE simpa.matriculas (
    aluno_id BIGINT NOT NULL,
    turma_id BIGINT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (aluno_id, turma_id),
    CONSTRAINT fk_matricula_aluno FOREIGN KEY (aluno_id)
        REFERENCES simpa.alunos (id) ON DELETE RESTRICT,
    CONSTRAINT fk_matricula_turma FOREIGN KEY (turma_id)
        REFERENCES simpa.turmas (id) ON DELETE RESTRICT
);

-- 6. Turma-disciplinas: disciplinas oferecidas em cada turma.
CREATE TABLE simpa.turma_disciplinas (
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    PRIMARY KEY (turma_id, disciplina_id),
    CONSTRAINT fk_oferta_turma FOREIGN KEY (turma_id)
        REFERENCES simpa.turmas (id) ON DELETE RESTRICT,
    CONSTRAINT fk_oferta_disciplina FOREIGN KEY (disciplina_id)
        REFERENCES simpa.disciplinas (id) ON DELETE RESTRICT
);

-- 7. Registros: um resultado consolidado por aluno e oferta.
CREATE TABLE simpa.registros_academicos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL,
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    nota NUMERIC NOT NULL,
    frequencia NUMERIC NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_registro_nota CHECK (nota BETWEEN 0 AND 10),
    CONSTRAINT ck_registro_frequencia
        CHECK (frequencia BETWEEN 0 AND 100),
    CONSTRAINT uq_registro_oferta
        UNIQUE (aluno_id, turma_id, disciplina_id),
    CONSTRAINT fk_registro_matricula
        FOREIGN KEY (aluno_id, turma_id)
        REFERENCES simpa.matriculas (aluno_id, turma_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_registro_oferta
        FOREIGN KEY (turma_id, disciplina_id)
        REFERENCES simpa.turma_disciplinas
            (turma_id, disciplina_id)
        ON DELETE RESTRICT
);

-- 8. Importacoes: resumo de cada carga da base inicial.
CREATE TABLE simpa.importacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome_arquivo TEXT NOT NULL CHECK (btrim(nome_arquivo) <> ''),
    iniciada_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada_em TIMESTAMPTZ,
    situacao VARCHAR(20) NOT NULL DEFAULT 'em_processamento'
        CHECK (situacao IN
            ('em_processamento', 'concluida', 'falha')),
    registros_lidos INTEGER NOT NULL DEFAULT 0
        CHECK (registros_lidos >= 0),
    registros_aceitos INTEGER NOT NULL DEFAULT 0
        CHECK (registros_aceitos >= 0),
    registros_com_erro INTEGER NOT NULL DEFAULT 0
        CHECK (registros_com_erro >= 0),
    CONSTRAINT ck_importacao_contagem CHECK (
        registros_aceitos::BIGINT + registros_com_erro
            <= registros_lidos
    ),
    CONSTRAINT ck_importacao_conclusao CHECK (
        situacao <> 'concluida' OR
        (finalizada_em IS NOT NULL AND
         registros_aceitos::BIGINT + registros_com_erro
            = registros_lidos)
    ),
    CONSTRAINT ck_importacao_datas CHECK (
        finalizada_em IS NULL OR finalizada_em >= iniciada_em
    )
);

-- 9. Erros: motivo da rejeicao de cada linha importada.
CREATE TABLE simpa.erros_importacao (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    importacao_id BIGINT NOT NULL,
    numero_linha INTEGER NOT NULL CHECK (numero_linha > 0),
    mensagem TEXT NOT NULL CHECK (btrim(mensagem) <> ''),
    CONSTRAINT fk_erro_importacao FOREIGN KEY (importacao_id)
        REFERENCES simpa.importacoes (id) ON DELETE RESTRICT,
    CONSTRAINT uq_erro_linha UNIQUE (importacao_id, numero_linha)
);

-- Indices para consultas por turma e disciplina.
CREATE INDEX idx_matriculas_turma
    ON simpa.matriculas (turma_id);
CREATE INDEX idx_turma_disciplinas_disciplina
    ON simpa.turma_disciplinas (disciplina_id);
CREATE INDEX idx_registros_turma_disciplina
    ON simpa.registros_academicos (turma_id, disciplina_id);
CREATE INDEX idx_registros_disciplina
    ON simpa.registros_academicos (disciplina_id);

COMMIT;
