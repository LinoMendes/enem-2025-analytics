-- Perfil socioeconômico dos participantes por faixa de renda e raça
SELECT
    ordem_renda,
    faixa_renda,
    cor_raca,
    COUNT(*) AS total_inscritos
FROM vw_participantes_enriquecido
GROUP BY ordem_renda, faixa_renda, cor_raca
ORDER BY ordem_renda, total_inscritos DESC;

-- Média geral e de Matemática por Dependência Administrativa da Escola
SELECT
    dependencia_adm_escola,
    COUNT(media_geral) AS total_presentes,
    ROUND(AVG(nu_nota_mt), 2) AS media_matematica,
    ROUND(AVG(nu_nota_redacao), 2) AS media_redacao,
    ROUND(AVG(media_geral), 2) AS media_geral
FROM vw_resultados_enriquecido
WHERE dependencia_adm_escola IS NOT NULL
GROUP BY dependencia_adm_escola
ORDER BY media_geral DESC;