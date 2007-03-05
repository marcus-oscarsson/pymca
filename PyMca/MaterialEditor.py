#/*##########################################################################
# Copyright (C) 2004-2007 European Synchrotron Radiation Facility
#
# This file is part of the PyMCA X-ray Fluorescence Toolkit developed at
# the ESRF by the Beamline Instrumentation Software Support (BLISS) group.
#
# This toolkit is free software; you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option) 
# any later version.
#
# PyMCA is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMCA; if not, write to the Free Software Foundation, Inc., 59 Temple Place,
# Suite 330, Boston, MA 02111-1307, USA.
#
# PyMCA follows the dual licensing model of Trolltech's Qt and Riverbank's PyQt
# and cannot be used as a free plugin for a non-free program. 
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license 
# is a problem to you.
#############################################################################*/
__revision__ = "$Revision: 1.12 $"
import sys
if 'qt' not in sys.modules:
    try:
        import PyQt4.Qt as qt
    except:
        import qt
else:
    import qt

DEBUG = 0
QTVERSION = qt.qVersion()
if QTVERSION < '3.0.0':
    import Myqttable as qttable
elif QTVERSION < '4.0.0':
    import qttable

import Elements
import ConfigDict
import os
import types

class MaterialEditor(qt.QWidget):
    def __init__(self, parent=None, name="Material Editor",
                 comments=True, height= 7):
        if QTVERSION < '4.0.0':
            qt.QWidget.__init__(self, parent, name)
            self.setCaption(name)
        else:
            qt.QWidget.__init__(self, parent)
            self.setWindowTitle(name)
        self.build(comments, height)

    def build(self,comments, height):
        layout = qt.QVBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.__hboxMaterialCombo   = qt.QWidget(self)
        hbox = self.__hboxMaterialCombo
        layout.addWidget(hbox)
        hboxlayout = qt.QHBoxLayout(hbox)
        hboxlayout.setMargin(0)
        hboxlayout.setSpacing(0)
        label = qt.QLabel(hbox)
        label.setText("Material")
        a = []
        for key in Elements.Material.keys():
            a.append(key)
        a.sort()
        self.matCombo = MaterialComboBox(hbox,options=a)
        #self.matCombo.setEditable(True)
        self.materialGUI = MaterialGUI(self,comments=comments, height=height)
        #HorizontalSpacer(hbox)
        if QTVERSION < '4.0.0':
            self.connect(self.matCombo,qt.PYSIGNAL('MaterialComboBoxSignal'),
                         self._comboSlot)
        else:
            self.connect(self.matCombo,qt.SIGNAL('MaterialComboBoxSignal'),
                         self._comboSlot)
        self.materialGUI.setCurrent(a[0])

        hboxlayout.addWidget(label)
        #hboxlayout.addWidget(HorizontalSpacer(hbox))
        hboxlayout.addWidget(self.matCombo)
        layout.addWidget(self.materialGUI)

    
    def importFile(self, filename):
        if not os.path.exists(filename):
            qt.QMessageBox.critical(self, "ERROR opening file",
                                    "File %s not found" % filename)
            return 1
        Elements.Material.read(filename)
        error = 0
        for material in Element.Material.keys():
            keys = Element.Material[material].keys()
            compoundList = []
            fractionList = []
            if "CompoundList" in  keys:
                compoundList = Element.Material[material]["CompoundList"]
            if "CompoundFraction" in  keys:
                compoundFraction = Element.Material[material]["CompoundFraction"]
            if  (compoundList == []) or (compoundFraction == []):
                #no message?
                error = 1
                del Element.Material[material]
                continue
            #I should try to calculate the attenuation at one energy ...
            try:
                d= Elements.getMaterialMassAttenuationCoefficients(compoundList,
                                                                   compoundFraction,
                                                                   energy = 10.0)
            except:
                #no message?
                error = 1
                del Element.Material[material]
                continue
        return error

    def _comboSlot(self, dict):
        self.materialGUI.setCurrent(dict['text'])

class MaterialComboBox(qt.QComboBox):
    def __init__(self,parent = None,name = None,fl = 0,
                 options=['1','2','3'],row=None,col=None):
        if row is None: row = 0
        if col is None: col = 0
        self.row = row
        self.col = col
        qt.QComboBox.__init__(self,parent)
        self.setOptions(options)
        self.ownValidator = MaterialValidator(self)
        self.setDuplicatesEnabled(False)
        self.setEditable(True)
        self._line = self.lineEdit()
        self.connect(self, qt.SIGNAL("activated(const QString &)"),
                     self._mySignal)
        if QTVERSION < '4.0.0':
            self.connect(self._line, qt.SIGNAL("returnPressed()"),
                         self._mySlot)
        else:
            self.connect(self._line, qt.SIGNAL("editingFinished()"),
                         self._mySlot)

    def setCurrentText(self, qstring):
        if QTVERSION < '3.0.0':
           self.lineEdit().setText(qstring)
        else:
            if QTVERSION < '4.0.0':
               qt.QComboBox.setCurrentText(self, qstring)
            else:
               qt.QComboBox.setEditText(self, qstring)

    def setOptions(self,options=['1','2','3']):
        self.clear()
        if QTVERSION < '4.0.0':
            self.insertStrList(options)
        else:
            for item in options:
                self.addItem(item)
                

    def getCurrent(self):
        return   self.currentItem(),str(self.currentText())

    def _mySignal(self, qstring0):
        qstring = qstring0
        (result, index) = self.ownValidator.validate(qstring,0)
        if result != self.ownValidator.Valid:
            qstring = self.ownValidator.fixup(qstring)
            (result, index) = self.ownValidator.validate(qstring,0)
        if result != self.ownValidator.Valid:
            text = str(qstring)
            msg=qt.QMessageBox.information( self, "Invalid Material %s" % str(qstring),
                                      "The material %s is not a valid Formula " \
                                      "nor a valid Material.\n" \
                                      "Do you want to define the material %s\n" % \
                                      (str(qstring), str(qstring)),
                                      qt.QMessageBox.Yes,qt.QMessageBox.No)
            if msg == qt.QMessageBox.No:
                if QTVERSION < '4.0.0':
                    self.setCurrentItem(0)
                else:
                    self.setCurrentIndex(0)
                for i in range(self.count()):
                    if QTVERSION <'4.0.0':
                        selftext = self.text(i)
                    else:
                        selftext = self.itemText(i)
                    if selftext == qstring0:
                        self.removeItem(i)
                return
            else:
                qstring = qstring0
        text = str(qstring)
        if Elements.isValidFormula(text): 
            msg =  qt.QMessageBox(self)
            msg.setIcon(qt.QMessageBox.Critical)
            msg.setText("Invalid Material Name %s\n" % text + \
                        "The material is a valid Formula.\n " \
                        "There is no need to define it.")
            if QTVERSION < '4.0.0':
                msg.exec_loop()
            else:
                msg.exec_()
            self.setCurrentItem(0)
            for i in range(self.count()):
                if QTVERSION <'4.0.0':
                    selftext = self.text(i)
                else:
                    selftext = self.itemText(i)
                if selftext == qstring0:
                    self.removeItem(i)
                    break                
            return            
        self.setCurrentText(text)
        dict = {}
        dict['event'] = 'activated'
        dict['row']   = self.row
        dict['col']   = self.col
        dict['text']  = text
        if qstring0 != qstring:
            self.removeItem(self.count()-1)
        insert = True
        for i in range(self.count()):
            if QTVERSION <'4.0.0':
                selftext = self.text(i)
            else:
                selftext = self.itemText(i)
            if qstring == selftext:
                insert = False
        if insert:
            if QTVERSION < '4.0.0':
                self.insertItem(qstring,-1)
            else:
                self.insertItem(self.count(), qstring)
                
        if QTVERSION < '3.0.0':
            pass
        else:
            if self.lineEdit() is not None:
                if QTVERSION < '4.0.0':
                    self.lineEdit().setPaletteBackgroundColor(qt.QColor("white"))
                
        if QTVERSION < '4.0.0':
            self.emit(qt.PYSIGNAL('MaterialComboBoxSignal'),(dict,))
        else:
            self.emit(qt.SIGNAL('MaterialComboBoxSignal'), (dict))

    def focusInEvent(self,event):
        if QTVERSION < '3.0.0':
            pass
        else:
            if self.lineEdit() is not None:
                if QTVERSION < '4.0.0':
                    self.lineEditBackgroundColor = self.lineEdit().paletteBackgroundColor()
                    self.lineEdit().setPaletteBackgroundColor(qt.QColor('yellow'))
    
    def _mySlot(self):
        if QTVERSION < '3.0.0':
            pass
        else:
            if QTVERSION < '4.0.0':
                self.lineEdit().setPaletteBackgroundColor(qt.QColor("white"))
        self._mySignal(self.currentText())

class MaterialValidator(qt.QValidator):
    def __init__(self, *var):
        qt.QValidator.__init__(self, *var)
        if QTVERSION >= '4.0.0':
            self.Valid = self.Acceptable

        
    def fixup(self, qstring):
        if qstring is None: return None
        text = str(qstring)
        key  = Elements.getMaterialKey(text) 
        if key is not None:
            return qt.QString(key)
        else:
            return qstring

    def validate(self, qstring, pos):
        text = str(qstring)
        if Elements.isValidFormula(text):
            return (self.Valid, pos)
        elif Elements.isValidMaterial(text):
            return (self.Valid, pos)
        else:
            return (self.Invalid,pos)

class MaterialGUI(qt.QWidget):
    def __init__(self, parent=None, name="New Material",default={},
                 comments=True, height=10):
        if QTVERSION < '4.0.0':
            qt.QWidget.__init__(self, parent, name)
            self.setCaption(name)
        else:
            qt.QWidget.__init__(self, parent)
            self.setWindowTitle(name)
        self._default = default
        self._setCurrentDefault()
        for key in default.keys():
            if key in self._current:
                self._current[key] = self._default[key]
        self.__lastRow    = None
        self.__lastColumn = None
        self.__fillingValues = True
        self.build(comments,height)
        
    def _setCurrentDefault(self):
        self._current = {'Comment':"New Material",
                         'CompoundList':[],
                         'CompoundFraction':[1.0],
                         'Density':1.0,
                         'Thickness':1.0}
        
    def build(self,comments="True",height=3):
        layout = qt.QVBoxLayout(self)
        layout.setMargin(0)
        layout.setSpacing(0)
        self.__comments = comments
        commentsHBox   = qt.QWidget(self)
        layout.addWidget(commentsHBox)
        commentsHBoxLayout = qt.QHBoxLayout(commentsHBox)
        commentsHBoxLayout.setMargin(0)
        commentsHBoxLayout.setSpacing(0)

        tableContainer = qt.QWidget(commentsHBox)
        commentsHBoxLayout.addWidget(tableContainer)
        tableContainerLayout = qt.QVBoxLayout(tableContainer)
        tableContainerLayout.setMargin(0)
        tableContainerLayout.setSpacing(0)
        self.__hboxTableContainer = qt.QWidget(tableContainer)
        hbox = self.__hboxTableContainer
        tableContainerLayout.addWidget(hbox)
        hboxLayout = qt.QHBoxLayout(hbox)
        hboxLayout.setMargin(0)
        hboxLayout.setSpacing(0)
        numberLabel  = qt.QLabel(hbox)
        hboxLayout.addWidget(numberLabel)
        numberLabel.setText("Number  of  Compounds:")
        if QTVERSION < '4.0.0':
            numberLabel.setAlignment(qt.QLabel.WordBreak | qt.QLabel.AlignVCenter)
        else:
            numberLabel.setAlignment(qt.Qt.AlignVCenter)
        self.__numberSpin  = qt.QSpinBox(hbox)
        hboxLayout.addWidget(self.__numberSpin)
        if QTVERSION < '4.0.0':
            self.__numberSpin.setMinValue(1)
            self.__numberSpin.setMaxValue(20)
        else:
            self.__numberSpin.setMinimum(1)
            self.__numberSpin.setMaximum(20)
        self.__numberSpin.setValue(1)
        if QTVERSION < '4.0.0':
            self.__table = qttable.QTable(tableContainer)
            self.__table.setNumRows(1)
            self.__table.setNumCols(2)
        else:
            self.__table = qt.QTableWidget(tableContainer)
            self.__table.setRowCount(1)
            self.__table.setColumnCount(2)
        tableContainerLayout.addWidget(self.__table)
        self.__table.setMinimumHeight((height)*self.__table.horizontalHeader().sizeHint().height())
        self.__table.setMaximumHeight((height)*self.__table.horizontalHeader().sizeHint().height())
        self.__table.setMinimumWidth(1*self.__table.sizeHint().width())
        self.__table.setMaximumWidth(1*self.__table.sizeHint().width())
        #self.__table.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Fixed,qt.QSizePolicy.Fixed))
        if QTVERSION < '4.0.0':
            self.__table.setVScrollBarMode(self.__table.AlwaysOn)
            self.__table.horizontalHeader().setClickEnabled(False)
            qt.QHeader.setLabel(self.__table.horizontalHeader(),0,"Material")
            qt.QHeader.setLabel(self.__table.horizontalHeader(),1,"Mass Fraction")
            self.__table.verticalHeader().hide()
            self.__table.setLeftMargin(0)
        else:
            labels = ["Material", "Mass Fraction"]
            for i in range(len(labels)):
                item = self.__table.horizontalHeaderItem(i)
                if item is None:
                    item = qt.QTableWidgetItem(labels[i],qt.QTableWidgetItem.Type)
                self.__table.setHorizontalHeaderItem(i,item)
        if QTVERSION < '4.1.0':
            self.__table.setSelectionMode(qttable.QTable.NoSelection)
        else:
            self.__table.setSelectionMode(qt.QTableWidget.NoSelection)
        if self.__comments:
            vbox = qt.QWidget(commentsHBox)
            commentsHBoxLayout.addWidget(vbox)
            vboxLayout = qt.QVBoxLayout(vbox)
            
            #default thickness and density
            self.__gridVBox = qt.QWidget(vbox)
            grid = self.__gridVBox
            vboxLayout.addWidget(grid)
            if QTVERSION < '4.0.0':
                gridLayout = qt.QGridLayout(grid, 2, 2, 11, 4)
            else:
                gridLayout = qt.QGridLayout(grid)
                gridLayout.setMargin(11)
                gridLayout.setSpacing(4)
            
            densityLabel  = qt.QLabel(grid)
            gridLayout.addWidget(densityLabel, 0, 0)
            densityLabel.setText("Default Density (g/cm3):")
            if QTVERSION < '4.0.0':
                densityLabel.setAlignment(qt.QLabel.WordBreak | qt.QLabel.AlignVCenter)
                self.__densityLine  = MyQLineEdit(grid)
            else:
                densityLabel.setAlignment(qt.Qt.AlignVCenter)
                self.__densityLine  = qt.QLineEdit(grid)
            self.__densityLine.setReadOnly(False)
            gridLayout.addWidget(self.__densityLine, 0, 1)

            thicknessLabel  = qt.QLabel(grid)
            gridLayout.addWidget(thicknessLabel, 1, 0)
            thicknessLabel.setText("Default  Thickness  (cm):")
            if QTVERSION < '4.0.0':
                thicknessLabel.setAlignment(qt.QLabel.WordBreak | qt.QLabel.AlignVCenter)
                self.__thicknessLine  = MyQLineEdit(grid)
            else:
                thicknessLabel.setAlignment(qt.Qt.AlignVCenter)
                self.__thicknessLine  = qt.QLineEdit(grid)
            gridLayout.addWidget(self.__thicknessLine, 1, 1)
            self.__thicknessLine.setReadOnly(False)
            if QTVERSION < '4.0.0':
                self.connect(self.__densityLine,qt.SIGNAL('returnPressed()'),
                             self.__densitySlot)      
                self.connect(self.__thicknessLine,qt.SIGNAL('returnPressed()'),
                         self.__thicknessSlot)
            else:
                self.connect(self.__densityLine,qt.SIGNAL('editingFinished()'),
                             self.__densitySlot)      
                self.connect(self.__thicknessLine,qt.SIGNAL('editingFinished()'),
                         self.__thicknessSlot)
            vboxLayout.addWidget(VerticalSpacer(vbox))
            
        if self.__comments:
            #comment
            nameHBox       = qt.QWidget(self)
            nameHBoxLayout = qt.QHBoxLayout(nameHBox)
            nameLabel      = qt.QLabel(nameHBox)
            nameHBoxLayout.addWidget(nameLabel)
            nameLabel.setText("Material Name/Comment:")
            if QTVERSION < '4.0.0':
                nameLabel.setAlignment(qt.QLabel.WordBreak | qt.QLabel.AlignVCenter)
            else:
                nameLabel.setAlignment(qt.Qt.AlignVCenter)
            nameHBoxLayout.addWidget(HorizontalSpacer(nameHBox))
            if QTVERSION < '4.0.0':
                self.__nameLine  = MyQLineEdit(nameHBox)
                self.connect(self.__nameLine,qt.SIGNAL('returnPressed()'),
                             self.__nameLineSlot)
            else:
                self.__nameLine  = qt.QLineEdit(nameHBox)
                self.connect(self.__nameLine,qt.SIGNAL('editingFinished()'),
                             self.__nameLineSlot)
            nameHBoxLayout.addWidget(self.__nameLine)
            self.__nameLine.setReadOnly(False)
            longtext="En un lugar de La Mancha, de cuyo nombre no quiero acordarme ..."
            self.__nameLine.setFixedWidth(self.__nameLine.fontMetrics().width(longtext))
            layout.addWidget(nameHBox)

        self.connect(self.__numberSpin,
                     qt.SIGNAL("valueChanged(int)"),
                     self.__numberSpinChanged)
        if QTVERSION < '4.0.0':
            self.connect(self.__table,
                         qt.SIGNAL("valueChanged(int,int)"),
                         self.__tableSlot)
            self.connect(self.__table,
                         qt.SIGNAL("currentChanged(int,int)"),
                         self.__tableSlot2)
        else:
            self.connect(self.__table,
                         qt.SIGNAL("cellChanged(int,int)"),
                         self.__tableSlot)
            self.connect(self.__table,
                         qt.SIGNAL("cellEntered(int,int)"),
                         self.__tableSlot2)

    def setCurrent(self, matkey0):
        if DEBUG:"setCurrent(self, matkey0) ", matkey0
        matkey = Elements.getMaterialKey(matkey0)
        if matkey is not None:
            self._current = Elements.Material[matkey]
        else:
            self._setCurrentDefault()
            Elements.Material[matkey0] = self._current
        self.__numberSpin.setFocus()
        try:
            self._fillValues()
        finally:
            self.__fillingValues = False
                    
        
    def _fillValues(self):
        if DEBUG: print "fillValues(self)"
        self.__fillingValues = True
        if self.__comments:
            self.__nameLine.setText("%s" % self._current['Comment'])
            try:
                self.__densityLine.setText("%.5g" % self._current['Density'])
            except:
                self.__densityLine.setText("")
            if 'Thickness' in self._current.keys():
                try:
                    self.__thicknessLine.setText("%.5g" % self._current['Thickness'])
                except:
                    self.__thicknessLine.setText("")
        if type(self._current['CompoundList']) != types.ListType:
            self._current['CompoundList'] = [self._current['CompoundList']] 
        if type(self._current['CompoundFraction']) != types.ListType:
            self._current['CompoundFraction'] = [self._current['CompoundFraction']] 
        self.__numberSpin.setValue(max(len(self._current['CompoundList']),1))
        row = 0
        for compound in  self._current['CompoundList']:
            if QTVERSION  < '4.0.0':
                self.__table.setText(row,0, compound)                
                self.__table.setText(row,1, "%.5g" % self._current['CompoundFraction'][row])
            else:
                item = self.__table.item(row,0)
                if item is None:
                    item = qt.QTableWidgetItem(compound,qt.QTableWidgetItem.Type)
                else:
                    item.setText(compound)
                self.__table.setItem(row,0,item)
                item = self.__table.item(row,1)
                if item is None:
                    item = qt.QTableWidgetItem("%.5g" % self._current['CompoundFraction'][row],
                                               qt.QTableWidgetItem.Type)
                else:
                    item.setText("%.5g" % self._current['CompoundFraction'][row])
                self.__table.setItem(row,1,item)
            row += 1
        self.__fillingValues = False

    if QTVERSION < '4.0.0':
        def _updateCurrent(self):
            if DEBUG:
                print "updateCurrent(self)"
                print "self._current before = ", self._current
            self._current['CompoundList']     = []
            self._current['CompoundFraction'] = []
            for i in range(self.__table.numRows()):
                txt0 = str(self.__table.text(i,0))
                txt1 = str(self.__table.text(i,1))
                if (len(txt0) > 0) and (len(txt1) > 0):
                    self._current['CompoundList'].append(txt0)
                    self._current['CompoundFraction'].append(float(txt1))
            if self.__comments:
                self._current['Comment'] = str(self.__nameLine.text())
            if DEBUG:
                print "self._current after = ", self._current
    else:
        def _updateCurrent(self):
            if DEBUG:
                print "updateCurrent(self)"
                print "self._current before = ", self._current

            self._current['CompoundList']     = []
            self._current['CompoundFraction'] = []
            for i in range(self.__table.rowCount()):
                item = self.__table.item(i, 0)
                if item is None:
                    item = qt.QTableWidgetItem("",
                                               qt.QTableWidgetItem.Type)
                txt0 = str(item.text())
                item = self.__table.item(i, 1)
                if item is None:
                    item = qt.QTableWidgetItem("",
                                               qt.QTableWidgetItem.Type)
                txt1 = str(item.text())
                if (len(txt0) > 0) and (len(txt1) > 0):
                    self._current['CompoundList'].append(txt0)
                    self._current['CompoundFraction'].append(float(txt1))
            if DEBUG:
                print "self._current after = ", self._current

    def __densitySlot(self):
        qstring = self.__densityLine.text()
        text = str(qstring)
        try:
            if len(text):
                value = float(str(qstring))
                self._current['Density'] = value
        except:
            msg=qt.QMessageBox(self.__densityLine)
            msg.setIcon(qt.QMessageBox.Critical)
            msg.setText("Invalid Float")
            if QTVERSION < '4.0.0':
                msg.exec_loop()
            else:
                msg.exec_()
            self.__densityLine.setFocus()
    
    def __thicknessSlot(self):
        qstring = self.__thicknessLine.text()
        text = str(qstring)
        try:
            if len(text):
                value = float(text)
                self._current['Thickness'] = value
        except:
            msg=qt.QMessageBox(self.__thicknessLine)
            msg.setIcon(qt.QMessageBox.Critical)
            msg.setText("Invalid Float")
            if QTVERSION < '4.0.0':
                msg.exec_loop()
            else:
                msg.exec_()
            self.__thicknessLine.setFocus()

    def __nameLineSlot(self):
        if DEBUG:print "__nameLineSlot(self)"
        qstring = self.__nameLine.text()
        text = str(qstring)
        self._current['Comment'] = text
    
    def __numberSpinChanged(self,value):
        #size = self.__table.size()
        if QTVERSION < '4.0.0':
            self.__table.setNumRows(value)
        else:
            self.__table.setRowCount(value)
            rheight = self.__table.horizontalHeader().sizeHint().height()
            nrows = self.__table.rowCount()
            for idx in range(nrows):
                self.__table.setRowHeight(idx, rheight)
        if len(self._current['CompoundList']) > value:
            self._current['CompoundList'] = self._current['CompoundList'][0:value]
        if len(self._current['CompoundFraction']) > value:
            self._current['CompoundFraction'] = self._current['CompoundFraction'][0:value]

    def __tableSlot(self,row, col):
        if self.__fillingValues:return
        if QTVERSION < '4.0.0':
            qstring = self.__table.text(row,col)
        else:
            item = self.__table.item(row, col)
            if item is not None:
                if DEBUG:print "table item is None"
                qstring = item.text()
            else:
                qstring = ""
        if col == 0:
            compound = str(qstring)
            if Elements.isValidFormula(compound):
                pass
            else:
                matkey  = Elements.getMaterialKey(compound)
                if matkey is not None:
                    if QTVERSION < '4.0.0':
                        self.__table.setText(row,
                                         col,
                                         matkey)
                    else:
                        item.setText(matkey)
                else:
                    msg=qt.QMessageBox(self.__table)
                    msg.setIcon(qt.QMessageBox.Critical)
                    msg.setText("Invalid Formula %s" % compound)
                    if QTVERSION < '4.0.0':
                        msg.exec_loop()
                    else:
                        msg.exec_()
                    self.__table.setCurrentCell(row, col)
                    return
        else:
            try:
                value = float(str(qstring))
            except:
                msg=qt.QMessageBox(self.__table)
                msg.setIcon(qt.QMessageBox.Critical)
                msg.setText("Invalid Float")
                if QTVERSION < '4.0.0':
                    msg.exec_loop()
                else:
                    msg.exec_()
                self.__table.setCurrentCell(row, col)
                return
        self._updateCurrent()

    def __tableSlot2(self,row, col):
        if self.__fillingValues:return
        if self.__lastRow is None:
            self.__lastRow = row
        
        if self.__lastColumn is None:
            self.__lastColumn = col

        qstring = self.__table.text(self.__lastRow, 
                                    self.__lastColumn)
        if self.__lastColumn == 0:
            compound     = str(qstring)
            if Elements.isValidFormula(compound):
                pass
            else:
                matkey  = Elements.getMaterialKey(compound)
                if matkey is not None:
                    self.__table.setText(self.__lastRow,
                                         self.__lastColumn,
                                         matkey)            
                else:
                    msg=qt.QMessageBox(self.__table)
                    msg.setIcon(qt.QMessageBox.Critical)
                    msg.setText("Invalid Formula %s" % compound)
                    if QTVERSION < '4.0.0':
                        msg.exec_loop()
                    else:
                        msg.exec_()
                    self.__table.setCurrentCell(self.__lastRow, self.__lastColumn)
                    return
        else:
            try:
                value = float(str(qstring))
            except:
                msg=qt.QMessageBox(self.__table)
                msg.setIcon(qt.QMessageBox.Critical)
                msg.setText("Invalid Float")
                if QTVERSION < '4.0.0':
                    msg.exec_loop()
                else:
                    msg.exec_()
                self.__table.setCurrentCell(self.__lastRow, self.__lastColumn)
                return
        self._updateCurrent()

class MyQLineEdit(qt.QLineEdit):
    def __init__(self,parent=None,name=None):
        qt.QLineEdit.__init__(self,parent)

    def focusInEvent(self,event):
        if QTVERSION < '4.0.0':
            self.setPaletteBackgroundColor(qt.QColor('yellow'))

    def focusOutEvent(self,event):
        if 0:
            self.setPaletteBackgroundColor(qt.QColor('white'))       
            if QTVERSION < '4.0.0':
                self.emit(qt.SIGNAL("returnPressed()"),())
            else:
                self.emit(qt.SIGNAL("returnPressed()"))
        
    def setPaletteBackgroundColor(self, qcolor):
        if QTVERSION < '3.0.0':
            palette = self.palette()
            palette.setColor(qt.QColorGroup.Base,qcolor)
            self.setPalette(palette)
            text = self.text()
            self.setText(text)
        elif QTVERSION < '4.0.0':
            qt.QLineEdit.setPaletteBackgroundColor(self,qcolor)
        else:
            if 0:
                palette = self.palette()
                role = self.backgroundRole()
                palette.setColor(role,qcolor)
                self.setPalette(palette)

class HorizontalSpacer(qt.QWidget):
    def __init__(self, *args):
        qt.QWidget.__init__(self, *args)

        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Fixed))

class VerticalSpacer(qt.QWidget):
    def __init__(self, *args):
        qt.QWidget.__init__(self, *args)
        self.setSizePolicy(qt.QSizePolicy(qt.QSizePolicy.Fixed,qt.QSizePolicy.Expanding))
        
if __name__ == "__main__":
    app = qt.QApplication([])
    qt.QObject.connect(app, qt.SIGNAL("lastWindowClosed()"),
                       app,qt.SLOT("quit()"))
    demo = MaterialEditor()
    if QTVERSION < '4.0.0':
        app.setMainWidget(demo)
        demo.show()
        app.exec_loop()
    else:
        demo.show()
        app.exec_()
