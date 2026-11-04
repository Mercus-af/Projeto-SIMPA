-- Evolução aditiva: os registros anteriores por bimestre são preservados.
BEGIN;
ALTER TABLE simpa.usuarios ADD COLUMN IF NOT EXISTS perfil TEXT NOT NULL DEFAULT 'professor'
    CHECK (perfil IN ('professor','aluno'));
ALTER TABLE simpa.usuarios ADD COLUMN IF NOT EXISTS aluno_id BIGINT REFERENCES simpa.alunos(id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuario_aluno ON simpa.usuarios(aluno_id) WHERE aluno_id IS NOT NULL;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='ck_usuario_perfil_aluno' AND conrelid='simpa.usuarios'::regclass) THEN
  ALTER TABLE simpa.usuarios ADD CONSTRAINT ck_usuario_perfil_aluno CHECK (perfil<>'aluno' OR aluno_id IS NOT NULL);
 END IF;
END $$;

CREATE TABLE IF NOT EXISTS simpa.professor_disciplinas (
    usuario_id BIGINT NOT NULL REFERENCES simpa.usuarios(id),
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    PRIMARY KEY(usuario_id,turma_id,disciplina_id),
    FOREIGN KEY(turma_id,disciplina_id) REFERENCES simpa.turma_disciplinas(turma_id,disciplina_id)
);
CREATE TABLE IF NOT EXISTS simpa.regras_va (
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    va SMALLINT NOT NULL CHECK(va BETWEEN 1 AND 3),
    max_atividades NUMERIC(8,2) NOT NULL DEFAULT 30 CHECK(max_atividades>=0),
    max_a360 NUMERIC(8,2) NOT NULL DEFAULT 10 CHECK(max_a360>=0),
    max_vrau NUMERIC(8,2) NOT NULL DEFAULT 30 CHECK(max_vrau>=0),
    max_afe NUMERIC(8,2) NOT NULL DEFAULT 30 CHECK(max_afe>=0),
    max_aps NUMERIC(8,2) NOT NULL DEFAULT 2 CHECK(max_aps>0),
    max_daily NUMERIC(8,2) NOT NULL DEFAULT 3 CHECK(max_daily>0),
    provisoria BOOLEAN NOT NULL DEFAULT TRUE,
    fechada BOOLEAN NOT NULL DEFAULT FALSE,
    fechada_em TIMESTAMPTZ,
    PRIMARY KEY(turma_id,disciplina_id,va),
    FOREIGN KEY(turma_id,disciplina_id) REFERENCES simpa.turma_disciplinas(turma_id,disciplina_id),
    CHECK(max_atividades+max_a360+max_vrau+max_afe=100)
);
CREATE TABLE IF NOT EXISTS simpa.atividades_va (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    va SMALLINT NOT NULL,
    tipo TEXT NOT NULL CHECK(tipo IN ('APS','DAILY','A360','VRAU','AFE')),
    titulo VARCHAR(150) NOT NULL CHECK(btrim(titulo)<>''),
    data_atividade DATE,
    maximo NUMERIC(8,2) NOT NULL CHECK(maximo>0 AND maximo<=100),
    criado_por BIGINT REFERENCES simpa.usuarios(id),
    FOREIGN KEY(turma_id,disciplina_id,va) REFERENCES simpa.regras_va(turma_id,disciplina_id,va)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_componente_va ON simpa.atividades_va(turma_id,disciplina_id,va,tipo)
    WHERE tipo IN ('A360','VRAU','AFE');
CREATE UNIQUE INDEX IF NOT EXISTS uq_atividade_titulo_va ON simpa.atividades_va(turma_id,disciplina_id,va,tipo,titulo);
CREATE TABLE IF NOT EXISTS simpa.notas_atividades (
    atividade_id BIGINT NOT NULL REFERENCES simpa.atividades_va(id),
    aluno_id BIGINT NOT NULL REFERENCES simpa.alunos(id),
    nota NUMERIC(8,2) CHECK(nota BETWEEN 0 AND 100),
    lancado_por BIGINT REFERENCES simpa.usuarios(id),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(atividade_id,aluno_id)
);
CREATE TABLE IF NOT EXISTS simpa.frequencias_va (
    aluno_id BIGINT NOT NULL,
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    va SMALLINT NOT NULL,
    aulas INTEGER NOT NULL CHECK(aulas>0),
    presencas INTEGER NOT NULL CHECK(presencas>=0 AND presencas<=aulas),
    PRIMARY KEY(aluno_id,turma_id,disciplina_id,va),
    FOREIGN KEY(aluno_id,turma_id) REFERENCES simpa.matriculas(aluno_id,turma_id),
    FOREIGN KEY(turma_id,disciplina_id,va) REFERENCES simpa.regras_va(turma_id,disciplina_id,va)
);
CREATE TABLE IF NOT EXISTS simpa.cargas_demo(chave TEXT PRIMARY KEY,criado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
COMMIT;
