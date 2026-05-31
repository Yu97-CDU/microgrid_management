from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPainter, QPen, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView

from nodes import ConnectionLine, MicrogridNode, NodePort


class MicrogridScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        self.grid_size = 20

    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        painter.fillRect(rect, QColor(248, 250, 252))

        light_pen = QPen(QColor(226, 232, 240), 1)
        strong_pen = QPen(QColor(203, 213, 225), 1)

        left = int(rect.left()) - int(rect.left()) % self.grid_size
        top = int(rect.top()) - int(rect.top()) % self.grid_size
        right = int(rect.right())
        bottom = int(rect.bottom())

        x = left
        while x < right:
            painter.setPen(strong_pen if x % 100 == 0 else light_pen)
            painter.drawLine(x, int(rect.top()), x, bottom)
            x += self.grid_size

        y = top
        while y < bottom:
            painter.setPen(strong_pen if y % 100 == 0 else light_pen)
            painter.drawLine(int(rect.left()), y, right, y)
            y += self.grid_size


class MicrogridCanvas(QGraphicsView):
    node_added = pyqtSignal(object)
    node_selected = pyqtSignal(object)
    connection_created = pyqtSignal(object, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = MicrogridScene(self)
        self.setScene(self.scene)
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._is_panning = False
        self._pan_start_pos = None
        self._temp_line: ConnectionLine | None = None
        self._line_start_port: NodePort | None = None
        self._node_counter: dict[str, int] = {}
        self.scene.selectionChanged.connect(self._emit_selected_node)

    def _emit_selected_node(self):
        for item in self.scene.selectedItems():
            if isinstance(item, MicrogridNode):
                self.node_selected.emit(item)
                return
            if isinstance(item, NodePort) and isinstance(item.parentItem(), MicrogridNode):
                self.node_selected.emit(item.parentItem())
                return

    def clear_all(self):
        self.scene.clear()
        self._node_counter.clear()

    def fit_all(self):
        rect = self.scene.itemsBoundingRect()
        if rect.isNull():
            return
        self.fitInView(rect.adjusted(-80, -80, 80, 80), Qt.AspectRatioMode.KeepAspectRatio)

    def add_node(self, symbol: str, scene_pos):
        count = self._node_counter.get(symbol, 0) + 1
        self._node_counter[symbol] = count
        node = MicrogridNode(name=f"{symbol}_{count}", symbol=symbol)
        node.setPos(scene_pos)
        self.scene.addItem(node)
        self.node_added.emit(node)
        return node

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-microgrid-symbol"):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-microgrid-symbol"):
            event.acceptProposedAction()
            return
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        mime = event.mimeData()
        if mime.hasFormat("application/x-microgrid-symbol"):
            symbol = bytes(mime.data("application/x-microgrid-symbol")).decode("utf-8")
            self.add_node(symbol, self.mapToScene(event.position().toPoint()))
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        zoom = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom, zoom)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if isinstance(item, NodePort):
                self._line_start_port = item
                self._temp_line = ConnectionLine(start_port=item)
                self._temp_line.set_end_pos(self.mapToScene(event.pos()))
                self.scene.addItem(self._temp_line)
                event.accept()
                return

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._is_panning = True
            self._pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._temp_line:
            self._temp_line.set_end_pos(self.mapToScene(event.pos()))
            event.accept()
            return

        if self._is_panning and self._pan_start_pos is not None:
            delta = event.pos() - self._pan_start_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start_pos = event.pos()
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._temp_line:
            item = self.itemAt(event.pos())
            if isinstance(item, NodePort) and item is not self._line_start_port and item.parentItem() is not self._line_start_port.parentItem():
                self._temp_line.end_port = item
                self._temp_line.update_path()
                self._line_start_port.add_edge(self._temp_line)
                item.add_edge(self._temp_line)
                self.connection_created.emit(self._temp_line, self._line_start_port.parentItem(), item.parentItem())
            else:
                self.scene.removeItem(self._temp_line)
            self._temp_line = None
            self._line_start_port = None
            event.accept()
            return

        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.delete_selected()
            event.accept()
            return
        super().keyPressEvent(event)

    def delete_selected(self):
        selected = list(self.scene.selectedItems())
        for item in selected:
            if isinstance(item, MicrogridNode):
                for port in item.ports:
                    for edge in list(port.edges):
                        self._remove_edge(edge)
                self.scene.removeItem(item)
            elif isinstance(item, ConnectionLine):
                self._remove_edge(item)

    def _remove_edge(self, edge: ConnectionLine):
        if edge.start_port:
            edge.start_port.remove_edge(edge)
        if edge.end_port:
            edge.end_port.remove_edge(edge)
        if edge.scene() is self.scene:
            self.scene.removeItem(edge)

    def extract_topology(self):
        import networkx as nx

        graph = nx.Graph()
        for item in self.scene.items():
            if isinstance(item, MicrogridNode):
                graph.add_node(item.name, symbol=item.symbol, type=item.comp_type, **item.data)
        for item in self.scene.items():
            if isinstance(item, ConnectionLine) and item.start_port and item.end_port:
                start = item.start_port.parentItem()
                end = item.end_port.parentItem()
                if isinstance(start, MicrogridNode) and isinstance(end, MicrogridNode):
                    graph.add_edge(start.name, end.name, **item.data)
        return graph

    def node_items(self) -> list[MicrogridNode]:
        return [item for item in self.scene.items() if isinstance(item, MicrogridNode)]

    def edge_items(self) -> list[tuple[ConnectionLine, str, str]]:
        edges = []
        for item in self.scene.items():
            if isinstance(item, ConnectionLine) and item.start_port and item.end_port:
                start = item.start_port.parentItem()
                end = item.end_port.parentItem()
                if isinstance(start, MicrogridNode) and isinstance(end, MicrogridNode):
                    edges.append((item, start.name, end.name))
        return edges
