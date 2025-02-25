import pandas as pd
import numpy as np
from debug_excel import AnalisadorExcel
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from datetime import datetime, timedelta
import warnings
import os
import json
warnings.filterwarnings('ignore')

class AnalisadorAvancado:
    def __init__(self, diretorio=None):
        """
        Inicializa o analisador avançado.
        
        Args:
            diretorio (str, optional): Diretório onde estão os arquivos Excel. 
                                     Se None, usa o diretório atual.
        """
        self.diretorio = diretorio or os.getcwd()
        
        # Caminhos dos arquivos
        self.arquivo_julio = os.path.join(self.diretorio, "(JULIO) LISTAS INDIVIDUAIS.xlsx")
        self.arquivo_leandro = os.path.join(self.diretorio, "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
        
        # Verificar existência dos arquivos
        for arquivo in [self.arquivo_julio, self.arquivo_leandro]:
            if not os.path.exists(arquivo):
                raise FileNotFoundError(f"Arquivo não encontrado: {arquivo}")
        
        # Inicializar analisadores
        try:
            self.analisador_julio = AnalisadorExcel(self.arquivo_julio)
            self.analisador_leandro = AnalisadorExcel(self.arquivo_leandro)
            
            # Carregar dados dos dois grupos
            self.dados_julio = self.analisador_julio.analisar_arquivo()
            self.dados_leandro = self.analisador_leandro.analisar_arquivo()
            
            # Métricas por colaborador
            self.metricas_julio = {}
            self.metricas_leandro = {}
            self.gargalos = {}
            self.ultima_analise = None
            self.historico_analises = []
            
            # Processar dados de cada colaborador
            for nome_aba, df in self.dados_julio.items():
                metricas = self.processar_dados_colaborador(nome_aba, df)
                if metricas:
                    self.metricas_julio[nome_aba] = metricas
            
            for nome_aba, df in self.dados_leandro.items():
                metricas = self.processar_dados_colaborador(nome_aba, df)
                if metricas:
                    self.metricas_leandro[nome_aba] = metricas
            
            # Registrar data e hora da análise
            self.ultima_analise = datetime.now()
            
            # Salvar histórico da análise
            self.historico_analises.append({
                'data': self.ultima_analise,
                'metricas_julio': self.metricas_julio.copy(),
                'metricas_leandro': self.metricas_leandro.copy()
            })
            
            # Manter apenas as últimas 10 análises
            if len(self.historico_analises) > 10:
                self.historico_analises = self.historico_analises[-10:]
            
        except Exception as e:
            raise RuntimeError(f"Erro ao inicializar analisadores: {str(e)}")
        
    def calcular_correlacao_volume_eficiencia(self):
        """Calcula a correlação entre volume de casos e eficiência para cada grupo"""
        print("\n=== Análise de Correlação Volume vs Eficiência ===")
        
        resultados = {}
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            volumes = []
            eficiencias = []
            
            for colab, dados in metricas.items():
                try:
                    volume = sum(dados['distribuicao_status'].values())
                    eficiencia = dados.get('taxa_eficiencia', 0)
                    if volume > 0:  # Evitar dados inválidos
                        volumes.append(volume)
                        eficiencias.append(eficiencia)
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Aviso: Dados inválidos para {colab}: {str(e)}")
                    continue
            
            if len(volumes) >= 2:  # Precisamos de pelo menos 2 pontos para correlação
                try:
                    correlacao = stats.pearsonr(volumes, eficiencias)
                    resultados[grupo] = {
                        'coeficiente': correlacao[0],
                        'p_valor': correlacao[1]
                    }
                    
                    print(f"\nGrupo {grupo}:")
                    print(f"Coeficiente de correlação: {correlacao[0]:.3f}")
                    print(f"P-valor: {correlacao[1]:.3f}")
                    
                    if correlacao[1] < 0.05:
                        if correlacao[0] > 0:
                            print("=> Correlação positiva significativa: Maior volume está associado a maior eficiência")
                        else:
                            print("=> Correlação negativa significativa: Maior volume está associado a menor eficiência")
                    else:
                        print("=> Não há correlação significativa entre volume e eficiência")
                except Exception as e:
                    print(f"Erro ao calcular correlação para grupo {grupo}: {str(e)}")
            else:
                print(f"\nGrupo {grupo}: Dados insuficientes para análise de correlação")
        
        return resultados
    
    def detectar_gargalos(self):
        """Detecta gargalos no processo baseado em diversos indicadores"""
        print("\n=== Detecção de Gargalos ===\n")
        
        def analisar_grupo(nome_grupo, metricas):
            tempos = []
            pendentes = []
            maior_pendencia = (0, '')
            
            for colab, dados in metricas.items():
                # Análise de tempo
                if 'tempo_medio' in dados:
                    tempos.append(dados['tempo_medio'])
                
                # Análise de pendências
                n_pendentes = dados['distribuicao_status'].get('PENDENTE', 0)
                pendentes.append(n_pendentes)
                if n_pendentes > maior_pendencia[0]:
                    maior_pendencia = (n_pendentes, colab)
            
            tempo_medio = np.mean(tempos) if tempos else 0
            desvio_padrao = np.std(tempos) if tempos else 0
            media_pendentes = np.mean(pendentes) if pendentes else 0
            
            # Atualizar estrutura de gargalos
            self.gargalos[nome_grupo] = {
                'tempo_medio': tempo_medio,
                'casos_pendentes': int(media_pendentes),
                'maior_gargalo': f"{maior_pendencia[1]} ({maior_pendencia[0]} casos)"
            }
            
            print(f"Grupo {nome_grupo}:")
            print(f"Tempo médio de resolução do grupo: {tempo_medio:.1f} dias")
            print(f"Desvio padrão: {desvio_padrao:.1f} dias\n")
            print(f"Média de casos pendentes: {media_pendentes:.1f}")
            print(f"Colaborador com mais pendências: {maior_pendencia[1]} ({maior_pendencia[0]} casos)\n")
        
        analisar_grupo('JULIO', self.metricas_julio)
        analisar_grupo('LEANDRO', self.metricas_leandro)
    
    def prever_tendencias(self):
        """Analisa tendências e faz previsões simples"""
        print("\n=== Análise de Tendências e Previsões ===")
        
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            print(f"\nGrupo {grupo}:")
            
            # Análise de tendências por colaborador
            for colab, dados in metricas.items():
                if 'tendencia' in dados:
                    tendencia = dados['tendencia']
                    print(f"\nColaborador: {colab}")
                    
                    # Interpretar coeficiente angular
                    slope = tendencia.get('direcao', '')
                    r2 = tendencia.get('r2', 0)
                    
                    if slope == "estável":
                        tendencia_str = "estável"
                    elif slope == "crescente":
                        tendencia_str = "crescente"
                    else:
                        tendencia_str = "decrescente"
                    
                    print(f"Tendência: {tendencia_str}")
                    print(f"R² = {r2:.3f}")
                    
                    # Fazer previsão para próxima semana
                    if r2 > 0.3:  # Só fazer previsão se o modelo tiver um ajuste razoável
                        ultima_eficiencia = dados['taxa_eficiencia']
                        previsao_proxima_semana = ultima_eficiencia + (slope * 7)  # 7 dias
                        print(f"Previsão de eficiência para próxima semana: {previsao_proxima_semana*100:.1f}%")
                        
                        if previsao_proxima_semana < ultima_eficiencia * 0.8:
                            print(" Alerta: Possível queda significativa na eficiência")
                        elif previsao_proxima_semana > ultima_eficiencia * 1.2:
                            print(" Expectativa de melhoria significativa na eficiência")

    def gerar_dashboard_html(self):
        """Gera um dashboard HTML com os resultados da análise"""
        
        # Criar o template HTML
        html_template = """<!DOCTYPE html>
<html>
<head>
    <title>Dashboard de Atividades</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .card { margin-bottom: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; margin-bottom: 20px; }
        .metric { font-size: 24px; font-weight: bold; }
        .historical-data { margin-top: 20px; }
        .historical-data table { width: 100%; }
        .historical-data th { background-color: #f8f9fa; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="header">
            <h1>Dashboard de Atividades</h1>
            <p>Última atualização: {data_atualizacao}</p>
        </div>
        
        <!-- Análise Atual -->
        <h2>Análise Atual</h2>
        <div class="row">
            <!-- Grupo Julio -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h2>Grupo Julio</h2>
                    </div>
                    <div class="card-body">
                        {metricas_julio}
                    </div>
                </div>
            </div>
            
            <!-- Grupo Leandro -->
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h2>Grupo Leandro</h2>
                    </div>
                    <div class="card-body">
                        {metricas_leandro}
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Gráficos -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h2>Análise de Produtividade por Data</h2>
                    </div>
                    <div class="card-body">
                        <div id="grafico_produtividade"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Histórico de Análises -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h2>Histórico de Análises</h2>
                    </div>
                    <div class="card-body">
                        <div class="historical-data">
                            {historico_analises}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {scripts_plotly}
    </script>
</body>
</html>"""
        
        # Função para gerar o HTML das métricas de um grupo
        def gerar_html_metricas(metricas):
            html = ""
            for colaborador, dados in metricas.items():
                if not dados:  # Skip if dados is None
                    continue
                    
                html += """<div class="card mb-3">
                    <div class="card-header">
                        <h3>{}</h3>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <h4>Volume Total</h4>
                                <p class="metric">{}</p>
                            </div>
                            <div class="col-md-6">
                                <h4>Taxa de Eficiência</h4>
                                <p class="metric">{}%</p>
                            </div>
                        </div>
                        
                        <h4>Distribuição de Status</h4>
                        <ul>
                """.format(colaborador, dados['total_registros'], dados['taxa_eficiencia'])
                
                for status, count in dados['distribuicao_status'].items():
                    percentual = (count / dados['total_registros']) * 100
                    html += "<li>{}: {} ({:.1f}%)</li>".format(status, count, percentual)
                
                html += """
                        </ul>
                        
                        <h4>Análise de Tendência</h4>
                """
                
                if 'tendencia' in dados:
                    html += """<p>Direção: {} (R² = {})</p>""".format(dados['tendencia']['direcao'], dados['tendencia']['r2'])
                else:
                    html += "<p>Sem dados suficientes para análise de tendência</p>"
                
                html += """
                    </div>
                </div>
                """
            
            return html

        # Função para gerar o HTML do histórico de análises
        def gerar_html_historico():
            if not self.historico_analises:
                return "<p>Nenhuma análise anterior registrada.</p>"
            
            html = """<table class="table table-striped">
                <thead>
                    <tr>
                        <th>Data da Análise</th>
                        <th>Grupo Julio</th>
                        <th>Grupo Leandro</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for analise in reversed(self.historico_analises):
                data = analise['data'].strftime("%d/%m/%Y %H:%M")
                metricas_julio = sum(dados['total_registros'] for dados in analise['metricas_julio'].values() if dados)
                metricas_leandro = sum(dados['total_registros'] for dados in analise['metricas_leandro'].values() if dados)
                
                html += """
                    <tr>
                        <td>{}</td>
                        <td>{} registros</td>
                        <td>{} registros</td>
                    </tr>
                """.format(data, metricas_julio, metricas_leandro)
            
            html += """
                </tbody>
            </table>
            """
            return html
        
        # Gerar gráficos com Plotly
        def gerar_scripts_plotly():
            scripts = []
            
            # Função para criar gráfico de linha para um grupo
            def criar_grafico_grupo(metricas, nome_grupo):
                dados_grafico = []
                
                for colaborador, dados in metricas.items():
                    if not dados or 'analise_diaria' not in dados:  # Skip if dados is None or doesn't have analise_diaria
                        continue
                        
                    x = []  # datas
                    y = []  # contagens
                    
                    for data, status_counts in dados['analise_diaria'].items():
                        x.append(data)
                        y.append(sum(status_counts.values()))
                    
                    if x and y:  # Only add if we have data points
                        dados_grafico.append({
                            'x': x,
                            'y': y,
                            'name': colaborador,
                            'type': 'scatter',
                            'mode': 'lines+markers'
                        })
                
                if not dados_grafico:  # If no data was added
                    return {
                        'data': [],
                        'layout': {
                            'title': f'Produtividade Diária - Grupo {nome_grupo}',
                            'xaxis': {'title': 'Data'},
                            'yaxis': {'title': 'Quantidade de Registros'},
                            'annotations': [{
                                'text': 'Sem dados suficientes para análise',
                                'showarrow': False,
                                'x': 0.5,
                                'y': 0.5,
                                'xref': 'paper',
                                'yref': 'paper'
                            }]
                        }
                    }
                
                return {
                    'data': dados_grafico,
                    'layout': {
                        'title': f'Produtividade Diária - Grupo {nome_grupo}',
                        'xaxis': {'title': 'Data', 'type': 'date'},
                        'yaxis': {'title': 'Quantidade de Registros'},
                        'showlegend': True
                    }
                }
            
            # Criar gráficos para cada grupo
            grafico_julio = criar_grafico_grupo(self.metricas_julio, 'Julio')
            grafico_leandro = criar_grafico_grupo(self.metricas_leandro, 'Leandro')
            
            # Adicionar os gráficos ao script
            scripts.append("""
                Plotly.newPlot('grafico_produtividade', 
                    {dados_julio}.data,
                    {dados_julio}.layout
                );
            """.format(
                dados_julio=json.dumps(grafico_julio),
            ))
            
            return "\n".join(scripts)
        
        # Gerar o HTML final
        html_final = html_template.format(
            data_atualizacao=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            metricas_julio=gerar_html_metricas(self.metricas_julio),
            metricas_leandro=gerar_html_metricas(self.metricas_leandro),
            historico_analises=gerar_html_historico(),
            scripts_plotly=gerar_scripts_plotly()
        )
        
        # Salvar o arquivo HTML
        with open('dashboard_atividades.html', 'w', encoding='utf-8') as f:
            f.write(html_final)
        
        print("\nDashboard gerado com sucesso! Abra o arquivo 'dashboard_atividades.html' no seu navegador.")

    def processar_dados_colaborador(self, nome, df):
        """Processa os dados de um colaborador específico"""
        try:
            # Converter datas para datetime
            df['Data'] = pd.to_datetime(df['DATA'], format='%d/%m/%Y', errors='coerce')
            
            # Remover registros com datas inválidas
            df = df.dropna(subset=['Data'])
            
            # Definir status com base nas colunas disponíveis
            df['Status'] = 'PENDENTE'  # Status padrão
            
            if 'RESOLUÇÃO' in df.columns:
                df.loc[df['RESOLUÇÃO'].notna(), 'Status'] = 'VERIFICADO'
            
            if 'ÚLTIMO PAGAMENTO' in df.columns:
                df.loc[df['ÚLTIMO PAGAMENTO'].notna(), 'Status'] = 'QUITADO'
            
            # Calcular distribuição de status
            distribuicao = df['Status'].value_counts().to_dict()
            total_registros = len(df)
            
            # Análise por data
            analise_diaria = {}
            for data, grupo in df.groupby('Data'):
                data_str = data.strftime('%Y-%m-%d')
                status_counts = grupo['Status'].value_counts().to_dict()
                analise_diaria[data_str] = status_counts

            # Calcular médias diárias
            dias_unicos = df['Data'].nunique()
            medias_diarias = {status: round(count/dias_unicos, 1) 
                            for status, count in distribuicao.items()}

            # Análise de tendências
            df_tendencia = df.groupby('Data').size().reset_index()
            if len(df_tendencia) > 1:
                X = np.arange(len(df_tendencia)).reshape(-1, 1)
                y = df_tendencia[0].values
                reg = LinearRegression().fit(X, y)
                r2 = reg.score(X, y)
                tendencia = 'crescente' if reg.coef_[0] > 0 else 'decrescente'
            else:
                tendencia = 'estável'
                r2 = 0

            # Análise semanal
            df['DiaSemana'] = df['Data'].dt.day_name()
            padrao_semanal = df['DiaSemana'].value_counts().to_dict()

            # Calcular taxa de eficiência
            total_processados = sum(v for k, v in distribuicao.items() 
                                  if k in ['VERIFICADO', 'QUITADO'])
            taxa_eficiencia = (total_processados / total_registros) * 100 if total_registros > 0 else 0

            return {
                'total_registros': total_registros,
                'distribuicao_status': distribuicao,
                'medias_diarias': medias_diarias,
                'tendencia': {
                    'direcao': tendencia,
                    'r2': round(r2, 3)
                },
                'padrao_semanal': padrao_semanal,
                'taxa_eficiencia': round(taxa_eficiencia, 1),
                'analise_diaria': analise_diaria
            }
        except Exception as e:
            print(f"Erro ao processar aba {nome}: {str(e)}")
            return None

if __name__ == "__main__":
    analisador = AnalisadorAvancado()
    
    print("\nANÁLISE AVANÇADA DE DESEMPENHO")
    print("=" * 50 + "\n")
    
    # Executar análises
    analisador.calcular_correlacao_volume_eficiencia()
    analisador.detectar_gargalos()
    analisador.prever_tendencias()
    
    # Gerar dashboard HTML
    analisador.gerar_dashboard_html()
