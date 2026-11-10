"""Excel-like fill handle and fill down/right shared by entry tables."""
from PySide6.QtCore import Qt,QRect,QSignalBlocker,QTimer
from PySide6.QtGui import QColor,QPainter,QPen,QUndoStack,QUndoCommand
from PySide6.QtWidgets import QTableWidgetItem,QTableWidgetSelectionRange
from .fill_series import series

class SpreadsheetFill:
    def init_fill(self):
        self._fill_seed=None;self._fill_target=None;self.setMouseTracking(True)
        self.itemSelectionChanged.connect(self.viewport().update)
        self._history_restoring=False;self.undo_stack=QUndoStack(self);self.undo_stack.setUndoLimit(20)
        self.history_timer=QTimer(self);self.history_timer.setSingleShot(True);self.history_timer.timeout.connect(self.commit_history)
        self._history_before=self.capture_cells();self.itemChanged.connect(self.queue_history)
        if hasattr(self,'rows_edited'):self.rows_edited.connect(self.queue_history)
    def capture_cells(self):
        data={}
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                item=self.item(row,col)
                if item and (item.text() or item.data(Qt.ItemDataRole.UserRole) is not None):data[row,col]=(item.text(),item.data(Qt.ItemDataRole.UserRole))
        return self.rowCount(),data
    def reset_history(self):
        self.history_timer.stop();self.undo_stack.clear();self._history_before=self.capture_cells()
    def queue_history(self,*args):
        if not self._history_restoring:self.history_timer.start(0)
    def commit_history(self):
        self.history_timer.stop();after=self.capture_cells()
        if after!=self._history_before:self.undo_stack.push(CellEdit(self,self._history_before,after))
        self._history_before=after
    def restore_cells(self,state):
        self._history_restoring=True
        try:
            with QSignalBlocker(self):
                self.clearContents();self.setRowCount(state[0])
                for (row,col),(text,role) in state[1].items():
                    item=QTableWidgetItem(text);item.setData(Qt.ItemDataRole.UserRole,role);self.setItem(row,col,item)
                if hasattr(self,'update_row'):
                    for row in range(self.rowCount()):self.update_row(row)
            if hasattr(self,'rows_edited'):self.rows_edited.emit()
            self._history_before=self.capture_cells()
        finally:self._history_restoring=False
    def undo_cells(self):self.commit_history();self.undo_stack.undo()
    def redo_cells(self):self.commit_history();self.undo_stack.redo()
    def selection_box(self):
        ranges=self.selectedRanges()
        if len(ranges)!=1:return None
        r=ranges[0];return (r.topRow(),r.leftColumn(),r.bottomRow(),r.rightColumn())
    def handle_rect(self):
        box=self.selection_box()
        if box is None:return QRect()
        top,left,bottom,right=box
        while right>=left and self.isColumnHidden(right):right-=1
        index=self.model().index(bottom,right);rect=self.visualRect(index)
        return QRect(rect.right()-4,rect.bottom()-4,8,8) if right>=left else QRect()
    def paintEvent(self,event):
        super().paintEvent(event)
        painter=QPainter(self.viewport());painter.setPen(QPen(QColor('#177E89'),2))
        if self._fill_target:
            a,b,c,d=self._fill_target;rect=self.visualRect(self.model().index(a,b)).united(self.visualRect(self.model().index(c,d)));painter.drawRect(rect.adjusted(1,1,-1,-1))
        handle=self.handle_rect()
        if not handle.isEmpty():painter.fillRect(handle,QColor('#177E89'))
        painter.end()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.handle_rect().adjusted(-3,-3,3,3).contains(event.position().toPoint()) and self.selection_box():
            self._fill_seed=self.selection_box();self._fill_target=None;event.accept();return
        super().mousePressEvent(event)
    def mouseMoveEvent(self,event):
        if self._fill_seed:
            point=event.position().toPoint()
            if point.y()>self.viewport().height()-18:self.verticalScrollBar().setValue(self.verticalScrollBar().value()+1)
            elif point.y()<18:self.verticalScrollBar().setValue(self.verticalScrollBar().value()-1)
            if point.x()>self.viewport().width()-18:self.horizontalScrollBar().setValue(self.horizontalScrollBar().value()+12)
            index=self.indexAt(point)
            if index.isValid():
                a,b,c,d=self._fill_seed
                if index.row()>c:self._fill_target=(a,b,index.row(),d)
                elif index.column()>d:self._fill_target=(a,b,c,index.column())
                else:self._fill_target=None
            self.viewport().update();event.accept();return
        self.viewport().setCursor(Qt.CursorShape.CrossCursor if self.selection_box() and self.handle_rect().adjusted(-3,-3,3,3).contains(event.position().toPoint()) else Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event):
        if self._fill_seed:
            seed,target=self._fill_seed,self._fill_target;self._fill_seed=None;self._fill_target=None
            if target:self.fill_range(seed,target,copy_only=bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier))
            self.viewport().update();event.accept();return
        super().mouseReleaseEvent(event)
    def fill_range(self,seed,target,copy_only=False):
        a,b,c,d=seed;ta,tb,tc,td=target;changes=[]
        vertical=tc>c
        for fixed in range(b,d+1) if vertical else range(a,c+1):
            if vertical and self.isColumnHidden(fixed):continue
            coords=[(r,fixed) for r in range(a,c+1)] if vertical else [(fixed,col) for col in range(b,d+1) if not self.isColumnHidden(col)]
            dest=[(r,fixed) for r in range(c+1,tc+1)] if vertical else [(fixed,col) for col in range(d+1,td+1) if not self.isColumnHidden(col)]
            items=[self.item(r,col) for r,col in coords];texts=[i.text() if i else '' for i in items]
            values=series(texts,len(dest),copy_only)
            for n,((r,col),text) in enumerate(zip(dest,values)):
                source=items[n%len(items)];item=source.clone() if source else QTableWidgetItem('');item.setText(text);changes.append((r,col,item))
        with QSignalBlocker(self):
            for r,col,item in changes:self.setItem(r,col,item)
            if hasattr(self,'update_row'):
                for r in sorted({r for r,col,item in changes}):self.update_row(r)
        self.clearSelection();self.setRangeSelected(QTableWidgetSelectionRange(*target),True)
        if changes and hasattr(self,'rows_edited'):self.rows_edited.emit()
    def fill_down(self):
        box=self.selection_box()
        if box and box[2]>box[0]:self.fill_range((box[0],box[1],box[0],box[3]),box,True)
    def fill_right(self):
        box=self.selection_box()
        if box and box[3]>box[1]:self.fill_range((box[0],box[1],box[2],box[1]),box,True)


class CellEdit(QUndoCommand):
    def __init__(self,table,before,after):super().__init__('Edit cells');self.table=table;self.before=before;self.after=after;self.first=True
    def undo(self):self.table.restore_cells(self.before)
    def redo(self):
        if self.first:self.first=False
        else:self.table.restore_cells(self.after)
