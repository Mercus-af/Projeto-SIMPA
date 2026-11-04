-- Dataset sintetico do professor, separado das notas do curso de IA.
-- Executado em uma transacao pelo importador; nao executa o SQL recebido.
CREATE SCHEMA IF NOT EXISTS simpa_dataset;
CREATE TABLE IF NOT EXISTS simpa_dataset.cursos (
  curso_id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  grau TEXT NOT NULL,
  total_periodos INTEGER NOT NULL,
  disciplinas_por_periodo INTEGER NOT NULL,
  modalidade TEXT NOT NULL,
  cidade_sede TEXT NOT NULL,
  uf_sede TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simpa_dataset.periodos_curriculares (
  periodo_id INTEGER PRIMARY KEY,
  curso_id INTEGER NOT NULL REFERENCES simpa_dataset.cursos(curso_id),
  numero_periodo INTEGER NOT NULL,
  quantidade_disciplinas INTEGER NOT NULL,
  carga_horaria_prevista INTEGER NOT NULL,
  UNIQUE (curso_id, numero_periodo)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.disciplinas (
  disciplina_id INTEGER PRIMARY KEY,
  periodo_id INTEGER NOT NULL REFERENCES simpa_dataset.periodos_curriculares(periodo_id),
  codigo TEXT NOT NULL,
  nome TEXT NOT NULL,
  carga_horaria INTEGER NOT NULL,
  tipo TEXT NOT NULL,
  indice_dificuldade_sintetico NUMERIC NOT NULL,
  UNIQUE (codigo)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.cidades (
  cidade_id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  uf TEXT NOT NULL,
  distancia_rodoviaria_aprox_km NUMERIC NOT NULL,
  UNIQUE (nome, uf)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.docentes (
  docente_id INTEGER PRIMARY KEY,
  nome_sintetico TEXT NOT NULL,
  titulacao TEXT NOT NULL,
  regime_trabalho TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simpa_dataset.alunos (
  aluno_id INTEGER PRIMARY KEY,
  codigo_academico TEXT NOT NULL,
  nome_sintetico TEXT NOT NULL,
  data_nascimento DATE NOT NULL,
  genero_autodeclarado TEXT NOT NULL,
  origem_dado TEXT NOT NULL,
  UNIQUE (codigo_academico)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.enderecos_alunos (
  endereco_id INTEGER PRIMARY KEY,
  aluno_id INTEGER NOT NULL REFERENCES simpa_dataset.alunos(aluno_id),
  cidade_id INTEGER NOT NULL REFERENCES simpa_dataset.cidades(cidade_id),
  logradouro_sintetico TEXT NOT NULL,
  numero_sintetico INTEGER NOT NULL,
  complemento_sintetico TEXT,
  bairro_sintetico TEXT NOT NULL,
  cep_sintetico TEXT NOT NULL,
  tempo_deslocamento_min INTEGER NOT NULL,
  UNIQUE (aluno_id)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.perfis_socioeconomicos (
  perfil_id INTEGER PRIMARY KEY,
  aluno_id INTEGER NOT NULL REFERENCES simpa_dataset.alunos(aluno_id),
  data_referencia DATE NOT NULL,
  renda_pessoal_mensal NUMERIC NOT NULL,
  renda_familiar_mensal NUMERIC NOT NULL,
  pessoas_domicilio INTEGER NOT NULL,
  trabalha INTEGER NOT NULL CHECK (trabalha IN (0,1)),
  horas_trabalho_semana INTEGER NOT NULL,
  dependentes INTEGER NOT NULL,
  primeira_geracao_superior INTEGER NOT NULL CHECK (primeira_geracao_superior IN (0,1)),
  qualidade_internet TEXT NOT NULL,
  escola_publica_origem INTEGER NOT NULL CHECK (escola_publica_origem IN (0,1)),
  UNIQUE (aluno_id, data_referencia)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.tipos_bolsa (
  tipo_bolsa_id INTEGER PRIMARY KEY,
  nome TEXT NOT NULL,
  categoria TEXT NOT NULL,
  percentual NUMERIC NOT NULL CHECK (percentual BETWEEN 0 AND 100)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.bolsas_alunos (
  bolsa_aluno_id INTEGER PRIMARY KEY,
  aluno_id INTEGER NOT NULL REFERENCES simpa_dataset.alunos(aluno_id),
  tipo_bolsa_id INTEGER NOT NULL REFERENCES simpa_dataset.tipos_bolsa(tipo_bolsa_id),
  data_inicio DATE NOT NULL,
  data_fim DATE,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simpa_dataset.matriculas_curso (
  matricula_curso_id INTEGER PRIMARY KEY,
  aluno_id INTEGER NOT NULL REFERENCES simpa_dataset.alunos(aluno_id),
  curso_id INTEGER NOT NULL REFERENCES simpa_dataset.cursos(curso_id),
  data_ingresso DATE NOT NULL,
  ano_ingresso INTEGER NOT NULL,
  semestre_ingresso INTEGER NOT NULL,
  periodo_atual INTEGER NOT NULL,
  turno TEXT NOT NULL,
  status TEXT NOT NULL,
  forma_ingresso TEXT NOT NULL,
  data_referencia DATE NOT NULL,
  UNIQUE (aluno_id, curso_id)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.turmas (
  turma_id INTEGER PRIMARY KEY,
  disciplina_id INTEGER NOT NULL REFERENCES simpa_dataset.disciplinas(disciplina_id),
  docente_id INTEGER NOT NULL REFERENCES simpa_dataset.docentes(docente_id),
  ano_letivo INTEGER NOT NULL,
  semestre_letivo INTEGER NOT NULL,
  codigo_turma TEXT NOT NULL,
  turno TEXT NOT NULL,
  modalidade TEXT NOT NULL,
  vagas INTEGER NOT NULL,
  carga_horaria INTEGER NOT NULL,
  UNIQUE (codigo_turma)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.registros_academicos (
  registro_id INTEGER PRIMARY KEY,
  matricula_curso_id INTEGER NOT NULL REFERENCES simpa_dataset.matriculas_curso(matricula_curso_id),
  turma_id INTEGER NOT NULL REFERENCES simpa_dataset.turmas(turma_id),
  tentativa INTEGER NOT NULL,
  situacao TEXT NOT NULL,
  nota_n1 NUMERIC NOT NULL CHECK (nota_n1 BETWEEN 0 AND 100),
  nota_n2 NUMERIC CHECK (nota_n2 BETWEEN 0 AND 100),
  nota_projeto NUMERIC CHECK (nota_projeto BETWEEN 0 AND 100),
  nota_parcial NUMERIC CHECK (nota_parcial BETWEEN 0 AND 100),
  nota_final NUMERIC CHECK (nota_final BETWEEN 0 AND 100),
  frequencia_percentual NUMERIC CHECK (frequencia_percentual BETWEEN 0 AND 100),
  faltas_horas INTEGER NOT NULL,
  carga_horaria_cursada INTEGER NOT NULL,
  data_atualizacao DATE NOT NULL,
  UNIQUE (matricula_curso_id, turma_id, tentativa)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.indicadores_risco (
  indicador_id INTEGER PRIMARY KEY,
  matricula_curso_id INTEGER NOT NULL REFERENCES simpa_dataset.matriculas_curso(matricula_curso_id),
  data_referencia DATE NOT NULL,
  media_historica NUMERIC NOT NULL CHECK (media_historica BETWEEN 0 AND 100),
  media_periodo_atual NUMERIC NOT NULL CHECK (media_periodo_atual BETWEEN 0 AND 100),
  frequencia_media NUMERIC NOT NULL CHECK (frequencia_media BETWEEN 0 AND 100),
  reprovacoes INTEGER NOT NULL,
  tendencia_nota_por_periodo NUMERIC NOT NULL,
  score_risco_percentual NUMERIC NOT NULL CHECK (score_risco_percentual BETWEEN 0 AND 100),
  classificacao_risco TEXT NOT NULL,
  motivos_risco TEXT NOT NULL,
  UNIQUE (matricula_curso_id, data_referencia)
);

CREATE TABLE IF NOT EXISTS simpa_dataset.desfechos_alunos (
  desfecho_id INTEGER PRIMARY KEY,
  matricula_curso_id INTEGER NOT NULL REFERENCES simpa_dataset.matriculas_curso(matricula_curso_id),
  inicio_janela DATE NOT NULL,
  fim_janela DATE NOT NULL,
  evasao_observada INTEGER NOT NULL CHECK (evasao_observada IN (0,1)),
  tipo_desfecho TEXT NOT NULL,
  data_evento_ou_censura DATE NOT NULL,
  UNIQUE (matricula_curso_id, inicio_janela)
);



CREATE TABLE IF NOT EXISTS simpa_dataset.cargas (identificador TEXT PRIMARY KEY, sha256 TEXT NOT NULL, origem TEXT NOT NULL, carregado_em TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP);
