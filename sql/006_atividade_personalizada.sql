-- Amplia os tipos aceitos, preservando atividades e notas existentes.
ALTER TABLE simpa.atividades_va DROP CONSTRAINT IF EXISTS atividades_va_tipo_check;
ALTER TABLE simpa.atividades_va ADD CONSTRAINT atividades_va_tipo_check
    CHECK (tipo IN ('APS','DAILY','PERSONALIZADA','A360','VRAU','AFE'));
