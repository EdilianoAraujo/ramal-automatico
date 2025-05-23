from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.core import *
from qgis.utils import iface

class MeuPluginRamal:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_action = None

    def initGui(self):
        self.plugin_action = QAction("Ativar Ramal Automático", self.iface.mainWindow())
        self.plugin_action.triggered.connect(self.ativar_ramal)
        self.iface.addPluginToMenu("Ramal Automático", self.plugin_action)

    def unload(self):
        self.iface.removePluginMenu("Ramal Automático", self.plugin_action)

    def ativar_ramal(self):
        try:
            layer_pe = QgsProject.instance().mapLayersByName("PONTO_DE_ENTREGA")[0]
            layer_pe.featureAdded.connect(self.criar_ramal_automatico)
            QMessageBox.information(None, "Ramal Automático", "Plugin ativado com sucesso.")
        except Exception as e:
            QMessageBox.critical(None, "Erro", f"Erro ao ativar o plugin: {str(e)}")

    def criar_ramal_automatico(self, fid):
        try:
            ponto_layer = QgsProject.instance().mapLayersByName("PONTO_DE_ENTREGA")[0]
            poste_layer = QgsProject.instance().mapLayersByName("LI_REDE_EC_POSTE")[0]
            ramal_layer = QgsProject.instance().mapLayersByName("RAMAL")[0]

            ponto = ponto_layer.getFeature(fid)

            if not ponto.geometry() or ponto.geometry().isEmpty():
                iface.messageBar().pushWarning("Erro", "Ponto de entrega sem geometria.")
                return

            id_poste = ponto["LI_REDE_EC_POSTE_ID"]
            if id_poste is None:
                iface.messageBar().pushWarning("Erro", "Campo LI_REDE_EC_POSTE_ID está vazio.")
                return

            expr = f'"fid" = {id_poste}'
            request = QgsFeatureRequest().setFilterExpression(expr)
            poste = next(poste_layer.getFeatures(request), None)

            if not poste or not poste.geometry() or poste.geometry().isEmpty():
                iface.messageBar().pushWarning("Erro", "Poste não encontrado ou sem geometria.")
                return

            linha = QgsGeometry.fromPolylineXY([
                poste.geometry().asPoint(),
                ponto.geometry().asPoint()
            ])
            nova_feat = QgsFeature(ramal_layer.fields())
            nova_feat.setGeometry(linha)
            nova_feat["MSLINK_PG"] = id_poste
            nova_feat["MSLINK_PE"] = ponto["fid"]

            with edit(ramal_layer):
                ramal_layer.addFeature(nova_feat)

            iface.messageBar().pushMessage("Ramal criado com sucesso", "", level=Qgis.Success)
        except Exception as e:
            iface.messageBar().pushCritical("Erro inesperado", str(e))
