import streamlit as st
import pandas as pd
import os
from auditoria_dados import AuditorDados
from analise_360 import Analise360

class DataAnalysisPipeline:
    def __init__(self):
        self.auditor = AuditorDados()
        self.analise360 = Analise360()
        
    def configurar_arquivos(self, arquivos):
        """Configura os arquivos para análise"""
        self.auditor.arquivos = arquivos
        self.analise360.configurar_arquivos(arquivos)
        
    def executar_pipeline(self):
        st.set_page_config(layout="wide", page_title="Pipeline de Análise de Dados")
        
        st.title("🔄 Pipeline de Análise de Dados")
        st.write("Sistema integrado de análise e auditoria de dados")
        
        # Sidebar para configuração
        with st.sidebar:
            st.title("⚙️ Configurações")
            upload_files = st.file_uploader(
                "Carregar arquivos Excel",
                type=['xlsx'],
                accept_multiple_files=True
            )
            
            if upload_files:
                arquivos = {}
                for file in upload_files:
                    # Salva temporariamente o arquivo
                    with open(os.path.join("temp", file.name), "wb") as f:
                        f.write(file.getbuffer())
                    arquivos[file.name.split('.')[0]] = os.path.join("temp", file.name)
                self.configurar_arquivos(arquivos)
            
            st.markdown("---")
            st.markdown("""
            ### 📚 Documentação
            
            **Módulos Disponíveis:**
            1. **Auditoria de Dados**
               - Análise de qualidade
               - Detecção de problemas
               - Métricas por aba
            
            2. **Análise 360**
               - Visão completa dos dados
               - Métricas avançadas
               - Relatórios detalhados
            """)
        
        # Tabs para diferentes análises
        tab1, tab2 = st.tabs(["🔍 Auditoria de Dados", "📊 Análise 360"])
        
        with tab1:
            if upload_files:
                self.auditor.mostrar_dashboard_auditoria()
            else:
                st.info("⚠️ Por favor, carregue os arquivos Excel para começar a análise")
        
        with tab2:
            if upload_files:
                self.analise360.mostrar_dashboard_360()
            else:
                st.info("⚠️ Por favor, carregue os arquivos Excel para começar a análise")

if __name__ == "__main__":
    # Cria diretório temporário se não existir
    os.makedirs("temp", exist_ok=True)
    
    # Executa o pipeline
    pipeline = DataAnalysisPipeline()
    pipeline.executar_pipeline()
