-- ============================================================================
-- TABELAS DE DOMÍNIO (LOOKUP) - DICIONÁRIO DE DADOS INEP / ENEM 2025
-- ============================================================================

-- 1. Domínio: Cor / Raça (TP_COR_RACA)
CREATE TABLE IF NOT EXISTS dom_cor_raca (
    codigo SMALLINT PRIMARY KEY,
    descricao VARCHAR(40) NOT NULL
);

INSERT INTO dom_cor_raca (codigo, descricao) VALUES
    (0, 'Não declarado'),
    (1, 'Branca'),
    (2, 'Preta'),
    (3, 'Parda'),
    (4, 'Amarela'),
    (5, 'Indígena'),
    (6, 'Não dispõe da informação')
ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao;

-- 2. Domínio: Sexo (TP_SEXO)
CREATE TABLE IF NOT EXISTS dom_sexo (
    codigo CHAR(1) PRIMARY KEY,
    descricao VARCHAR(20) NOT NULL
);

INSERT INTO dom_sexo (codigo, descricao) VALUES
    ('M', 'Masculino'),
    ('F', 'Feminino')
ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao;

-- 3. Domínio: Dependência Administrativa da Escola (TP_DEPENDENCIA_ADM_ESC)
CREATE TABLE IF NOT EXISTS dom_dependencia_adm (
    codigo SMALLINT PRIMARY KEY,
    descricao VARCHAR(30) NOT NULL
);

INSERT INTO dom_dependencia_adm (codigo, descricao) VALUES
    (1, 'Federal'),
    (2, 'Estadual'),
    (3, 'Municipal'),
    (4, 'Privada')
ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao;

-- 4. Domínio: Localização da Escola (TP_LOCALIZACAO_ESC)
CREATE TABLE IF NOT EXISTS dom_localizacao_esc (
    codigo SMALLINT PRIMARY KEY,
    descricao VARCHAR(20) NOT NULL
);

INSERT INTO dom_localizacao_esc (codigo, descricao) VALUES
    (1, 'Urbana'),
    (2, 'Rural')
ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao;

-- 5. Domínio: Faixa Etária (TP_FAIXA_ETARIA)
CREATE TABLE IF NOT EXISTS dom_faixa_etaria (
    codigo SMALLINT PRIMARY KEY,
    descricao VARCHAR(35) NOT NULL
);

INSERT INTO dom_faixa_etaria (codigo, descricao) VALUES
    (1, 'Menor de 17 anos'),
    (2, '17 anos'),
    (3, '18 anos'),
    (4, '19 anos'),
    (5, '20 anos'),
    (6, '21 anos'),
    (7, '22 anos'),
    (8, '23 anos'),
    (9, '24 anos'),
    (10, '25 anos'),
    (11, 'Entre 26 e 30 anos'),
    (12, 'Entre 31 e 35 anos'),
    (13, 'Entre 36 e 40 anos'),
    (14, 'Entre 41 e 45 anos'),
    (15, 'Entre 46 e 50 anos'),
    (16, 'Entre 51 e 55 anos'),
    (17, 'Entre 56 e 60 anos'),
    (18, 'Entre 61 e 65 anos'),
    (19, 'Entre 66 e 70 anos'),
    (20, 'Maior de 70 anos')
ON CONFLICT (codigo) DO UPDATE SET descricao = EXCLUDED.descricao;

-- 6. Domínio: Renda Familiar Mensal (Q006)
-- Nota: os valores exatos em R$ acompanham o salário mínimo do ano da edição (2025).
-- Aqui mantemos a ordem numérica das faixas (ordem_faixa) para facilitar gráficos e ordenações.
CREATE TABLE IF NOT EXISTS dom_renda_q006 (
    codigo CHAR(1) PRIMARY KEY,
    ordem_faixa SMALLINT NOT NULL,
    faixa_sm VARCHAR(40) NOT NULL,
    descricao_completa VARCHAR(100) NOT NULL
);

INSERT INTO dom_renda_q006 (codigo, ordem_faixa, faixa_sm, descricao_completa) VALUES
    ('A', 1,  'Nenhuma renda',        'Nenhuma renda'),
    ('B', 2,  'Até 1 SM',             'Até 1 salário mínimo'),
    ('C', 3,  'De 1 a 1,5 SM',        'Mais de 1 até 1,5 salário mínimo'),
    ('D', 4,  'De 1,5 a 2 SM',        'Mais de 1,5 até 2 salários mínimos'),
    ('E', 5,  'De 2 a 2,5 SM',        'Mais de 2 até 2,5 salários mínimos'),
    ('F', 6,  'De 2,5 a 3 SM',        'Mais de 2,5 até 3 salários mínimos'),
    ('G', 7,  'De 3 a 4 SM',          'Mais de 3 até 4 salários mínimos'),
    ('H', 8,  'De 4 a 5 SM',          'Mais de 4 até 5 salários mínimos'),
    ('I', 9,  'De 5 a 6 SM',          'Mais de 5 até 6 salários mínimos'),
    ('J', 10, 'De 6 a 7 SM',          'Mais de 6 até 7 salários mínimos'),
    ('K', 11, 'De 7 a 8 SM',          'Mais de 7 até 8 salários mínimos'),
    ('L', 12, 'De 8 a 9 SM',          'Mais de 8 até 9 salários mínimos'),
    ('M', 13, 'De 9 a 10 SM',         'Mais de 9 até 10 salários mínimos'),
    ('N', 14, 'De 10 a 12 SM',        'Mais de 10 até 12 salários mínimos'),
    ('O', 15, 'De 12 a 15 SM',        'Mais de 12 até 15 salários mínimos'),
    ('P', 16, 'De 15 a 20 SM',        'Mais de 15 até 20 salários mínimos'),
    ('Q', 17, 'Acima de 20 SM',       'Mais de 20 salários mínimos')
ON CONFLICT (codigo) DO UPDATE SET
    ordem_faixa = EXCLUDED.ordem_faixa,
    faixa_sm = EXCLUDED.faixa_sm,
    descricao_completa = EXCLUDED.descricao_completa;

-- ============================================================================
-- VIEWS ANALÍTICAS PRONTAS PARA CONSULTA (DBEAVER E JUPYTER)
-- ============================================================================

-- View 1: Participantes com todos os atributos traduzidos
CREATE OR REPLACE VIEW vw_participantes_enriquecido AS
SELECT
    p.nu_inscricao,
    p.nu_ano,
    fe.descricao AS faixa_etaria,
    sx.descricao AS sexo,
    cr.descricao AS cor_raca,
    CASE WHEN p.in_treineiro = 1 THEN 'Sim' ELSE 'Não' END AS treineiro,
    m.no_municipio AS municipio_prova,
    m.sg_uf AS uf_prova,
    r.ordem_faixa AS ordem_renda,
    r.faixa_sm AS faixa_renda,
    p.q005 AS moradores_residencia
FROM participantes p
LEFT JOIN dom_faixa_etaria fe ON p.tp_faixa_etaria = fe.codigo
LEFT JOIN dom_sexo sx         ON p.tp_sexo = sx.codigo
LEFT JOIN dom_cor_raca cr     ON p.tp_cor_raca = cr.codigo
LEFT JOIN municipios m        ON p.co_municipio_prova = m.co_municipio
LEFT JOIN dom_renda_q006 r    ON p.q006 = r.codigo;

-- View 2: Resultados com dados da escola, município e média geral calculada
CREATE OR REPLACE VIEW vw_resultados_enriquecido AS
SELECT
    res.nu_sequencial,
    res.co_escola,
    da.descricao AS dependencia_adm_escola,
    loc.descricao AS localizacao_escola,
    m_esc.no_municipio AS municipio_escola,
    m_esc.sg_uf AS uf_escola,
    m_prv.no_municipio AS municipio_prova,
    m_prv.sg_uf AS uf_prova,
    CASE res.tp_lingua WHEN 0 THEN 'Inglês' WHEN 1 THEN 'Espanhol' END AS lingua_estrangeira,
    res.nu_nota_cn,
    res.nu_nota_ch,
    res.nu_nota_lc,
    res.nu_nota_mt,
    res.nu_nota_redacao,
    -- Média simples das 5 áreas apenas para quem esteve presente nas 4 provas objetivas e não zerou redação por ausência
    CASE
        WHEN res.tp_presenca_cn = 1
         AND res.tp_presenca_ch = 1
         AND res.tp_presenca_lc = 1
         AND res.tp_presenca_mt = 1
         AND res.nu_nota_redacao IS NOT NULL
        THEN ROUND((res.nu_nota_cn + res.nu_nota_ch + res.nu_nota_lc + res.nu_nota_mt + res.nu_nota_redacao) / 5.0, 2)
        ELSE NULL
    END AS media_geral
FROM resultados res
LEFT JOIN escolas e              ON res.co_escola = e.co_escola
LEFT JOIN dom_dependencia_adm da ON e.tp_dependencia_adm_esc = da.codigo
LEFT JOIN dom_localizacao_esc loc ON e.tp_localizacao_esc = loc.codigo
LEFT JOIN municipios m_esc       ON e.co_municipio_esc = m_esc.co_municipio
LEFT JOIN municipios m_prv       ON res.co_municipio_prova = m_prv.co_municipio;