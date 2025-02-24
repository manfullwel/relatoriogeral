import sqlite3
from datetime import datetime
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name='analise_historica.db'):
        self.db_name = db_name
        self.init_database()
        
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        
        # Tabela de métricas diárias por colaborador
        c.execute('''
            CREATE TABLE IF NOT EXISTS metricas_colaborador (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_analise DATE,
                grupo TEXT,
                colaborador TEXT,
                total_registros INTEGER,
                taxa_eficiencia REAL,
                tempo_medio_resolucao REAL,
                casos_pendentes INTEGER,
                casos_verificados INTEGER,
                casos_analise INTEGER,
                tendencia_slope REAL,
                r_squared REAL
            )
        ''')
        
        # Tabela de alertas
        c.execute('''
            CREATE TABLE IF NOT EXISTS alertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_analise DATE,
                colaborador TEXT,
                tipo_alerta TEXT,
                descricao TEXT,
                resolvido BOOLEAN DEFAULT 0
            )
        ''')
        
        # Tabela de gargalos
        c.execute('''
            CREATE TABLE IF NOT EXISTS gargalos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_analise DATE,
                grupo TEXT,
                tipo_gargalo TEXT,
                metrica REAL,
                descricao TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def salvar_metricas(self, grupo, metricas):
        """Salva as métricas de um colaborador no banco"""
        conn = sqlite3.connect(self.db_name)
        data_atual = datetime.now().date()
        
        for colaborador, dados in metricas.items():
            try:
                conn.execute('''
                    INSERT INTO metricas_colaborador (
                        data_analise, grupo, colaborador, total_registros,
                        taxa_eficiencia, tempo_medio_resolucao, casos_pendentes,
                        casos_verificados, casos_analise, tendencia_slope, r_squared
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data_atual,
                    grupo,
                    colaborador,
                    sum(dados['distribuicao_status'].values()),
                    dados['taxa_eficiencia'],
                    dados.get('tempo_medio_resolucao', 0),
                    dados['distribuicao_status'].get('PENDENTE', 0),
                    dados['distribuicao_status'].get('VERIFICADO', 0),
                    dados['distribuicao_status'].get('ANÁLISE', 0),
                    dados.get('tendencias', {}).get('slope', 0),
                    dados.get('tendencias', {}).get('r_squared', 0)
                ))
            except Exception as e:
                print(f"Erro ao salvar métricas de {colaborador}: {str(e)}")
                
        conn.commit()
        conn.close()
        
    def salvar_alertas(self, alertas):
        """Salva os alertas no banco"""
        conn = sqlite3.connect(self.db_name)
        data_atual = datetime.now().date()
        
        for alerta in alertas:
            conn.execute('''
                INSERT INTO alertas (data_analise, colaborador, tipo_alerta, descricao)
                VALUES (?, ?, ?, ?)
            ''', (data_atual, alerta['colaborador'], alerta['tipo'], alerta['mensagem']))
            
        conn.commit()
        conn.close()
        
    def salvar_gargalos(self, gargalos):
        """Salva os gargalos identificados no banco"""
        conn = sqlite3.connect(self.db_name)
        data_atual = datetime.now().date()
        
        for gargalo in gargalos:
            conn.execute('''
                INSERT INTO gargalos (data_analise, grupo, tipo_gargalo, metrica, descricao)
                VALUES (?, ?, ?, ?, ?)
            ''', (data_atual, gargalo['grupo'], gargalo['tipo'], 
                  gargalo['metrica'], gargalo['descricao']))
            
        conn.commit()
        conn.close()
        
    def obter_historico_metricas(self, dias=30):
        """Retorna o histórico de métricas dos últimos X dias"""
        conn = sqlite3.connect(self.db_name)
        query = f'''
            SELECT * FROM metricas_colaborador 
            WHERE data_analise >= date('now', '-{dias} days')
            ORDER BY data_analise DESC, grupo, colaborador
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
        
    def obter_alertas_ativos(self):
        """Retorna alertas não resolvidos"""
        conn = sqlite3.connect(self.db_name)
        query = '''
            SELECT * FROM alertas 
            WHERE resolvido = 0
            ORDER BY data_analise DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
        
    def obter_gargalos_recentes(self, dias=7):
        """Retorna gargalos identificados nos últimos X dias"""
        conn = sqlite3.connect(self.db_name)
        query = f'''
            SELECT * FROM gargalos
            WHERE data_analise >= date('now', '-{dias} days')
            ORDER BY data_analise DESC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
