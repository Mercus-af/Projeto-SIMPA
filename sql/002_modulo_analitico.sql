-- Complemento aditivo do Marco 2. Pode ser executado novamente.
BEGIN;
ALTER TABLE simpa.turmas ADD COLUMN IF NOT EXISTS serie TEXT NOT NULL DEFAULT '';
ALTER TABLE simpa.turmas ADD COLUMN IF NOT EXISTS turno TEXT NOT NULL DEFAULT '';
ALTER TABLE simpa.turmas ADD COLUMN IF NOT EXISTS sala TEXT NOT NULL DEFAULT '';
ALTER TABLE simpa.disciplinas ADD COLUMN IF NOT EXISTS area TEXT NOT NULL DEFAULT 'Geral';
ALTER TABLE simpa.disciplinas ADD COLUMN IF NOT EXISTS aulas_por_bimestre INTEGER NOT NULL DEFAULT 20 CHECK (aulas_por_bimestre > 0);
CREATE TABLE IF NOT EXISTS simpa.avaliacoes (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    aluno_id BIGINT NOT NULL,
    turma_id BIGINT NOT NULL,
    disciplina_id BIGINT NOT NULL,
    bimestre SMALLINT NOT NULL CHECK (bimestre BETWEEN 1 AND 4),
    nota DOUBLE PRECISION CHECK (nota BETWEEN 0 AND 10),
    frequencia DOUBLE PRECISION CHECK (frequencia BETWEEN 0 AND 100),
    aulas_previstas DOUBLE PRECISION CHECK (aulas_previstas > 0),
    presencas DOUBLE PRECISION,
    UNIQUE (aluno_id, turma_id, disciplina_id, bimestre),
    FOREIGN KEY (aluno_id, turma_id) REFERENCES simpa.matriculas (aluno_id, turma_id),
    FOREIGN KEY (turma_id, disciplina_id) REFERENCES simpa.turma_disciplinas (turma_id, disciplina_id),
    CHECK ((aulas_previstas IS NULL AND presencas IS NULL) OR
           (aulas_previstas IS NOT NULL AND presencas IS NOT NULL AND
            presencas >= 0 AND presencas <= aulas_previstas))
);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_turma ON simpa.avaliacoes(turma_id, disciplina_id, bimestre);
COMMIT;
