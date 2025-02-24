import pandas as pd
import numpy as np
from debug_excel import AnalisadorExcel
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class AnalisadorAvancado:
    def __init__(self):
        self.analisador_julio = AnalisadorExcel("(JULIO) LISTAS INDIVIDUAIS.xlsx")
        self.analisador_leandro = AnalisadorExcel("(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx")
        
        # Carregar dados dos dois grupos
        self.dados_julio = self.analisador_julio.analisar_arquivo()
        self.dados_leandro = self.analisador_leandro.analisar_arquivo()
        
        # Métricas por colaborador
        self.metricas_julio = self.analisador_julio.colaboradores
        self.metricas_leandro = self.analisador_leandro.colaboradores
        
    def calcular_correlacao_volume_eficiencia(self):
        """Calcula a correlação entre volume de casos e eficiência para cada grupo"""
        print("\n=== Análise de Correlação Volume vs Eficiência ===")
        
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            volumes = []
            eficiencias = []
            
            for colab, dados in metricas.items():
                volume = sum(dados['distribuicao_status'].values())
                eficiencia = dados['taxa_eficiencia']
                volumes.append(volume)
                eficiencias.append(eficiencia)
            
            correlacao = stats.pearsonr(volumes, eficiencias)
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
    
    def detectar_gargalos(self):
        """Detecta gargalos no processo baseado em diversos indicadores"""
        print("\n=== Detecção de Gargalos ===")
        
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            print(f"\nGrupo {grupo}:")
            
            # Análise de tempo médio de resolução
            tempos_resolucao = []
            for colab, dados in metricas.items():
                if 'tempo_medio_resolucao' in dados and dados['tempo_medio_resolucao'] is not None:
                    tempos_resolucao.append(dados['tempo_medio_resolucao'])
            
            if tempos_resolucao:
                tempo_medio_grupo = np.mean(tempos_resolucao)
                tempo_std = np.std(tempos_resolucao)
                print(f"Tempo médio de resolução do grupo: {tempo_medio_grupo:.1f} dias")
                print(f"Desvio padrão: {tempo_std:.1f} dias")
                
                # Identificar colaboradores com tempo muito acima da média
                for colab, dados in metricas.items():
                    if 'tempo_medio_resolucao' in dados and dados['tempo_medio_resolucao'] is not None:
                        if dados['tempo_medio_resolucao'] > tempo_medio_grupo + 2*tempo_std:
                            print(f" Gargalo detectado: {colab} com tempo médio de {dados['tempo_medio_resolucao']:.1f} dias")
            
            # Análise de casos pendentes
            total_pendentes = 0
            max_pendentes = 0
            colab_max_pendentes = ""
            
            for colab, dados in metricas.items():
                pendentes = dados['distribuicao_status'].get('PENDENTE', 0)
                total_pendentes += pendentes
                if pendentes > max_pendentes:
                    max_pendentes = pendentes
                    colab_max_pendentes = colab
            
            media_pendentes = total_pendentes / len(metricas)
            print(f"\nMédia de casos pendentes: {media_pendentes:.1f}")
            print(f"Colaborador com mais pendências: {colab_max_pendentes} ({max_pendentes} casos)")
            
            if max_pendentes > media_pendentes * 1.5:
                print(f" Possível gargalo: {colab_max_pendentes} tem {max_pendentes:.0f} casos pendentes (50% acima da média)")
    
    def prever_tendencias(self):
        """Analisa tendências e faz previsões simples"""
        print("\n=== Análise de Tendências e Previsões ===")
        
        for grupo, metricas in [("JULIO", self.metricas_julio), ("LEANDRO", self.metricas_leandro)]:
            print(f"\nGrupo {grupo}:")
            
            # Análise de tendências por colaborador
            for colab, dados in metricas.items():
                if 'tendencias' in dados:
                    tendencia = dados['tendencias']
                    print(f"\nColaborador: {colab}")
                    
                    # Interpretar coeficiente angular
                    slope = tendencia.get('slope', 0)
                    r2 = tendencia.get('r_squared', 0)
                    
                    if abs(slope) < 0.001:
                        tendencia_str = "estável"
                    elif slope > 0:
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

if __name__ == "__main__":
    analisador = AnalisadorAvancado()
    
    print("\nANÁLISE AVANÇADA DE DESEMPENHO")
    print("=" * 50)
    
    # Executar análises
    analisador.calcular_correlacao_volume_eficiencia()
    analisador.detectar_gargalos()
    analisador.prever_tendencias()
