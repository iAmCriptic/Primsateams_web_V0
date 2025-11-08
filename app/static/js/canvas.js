/**
 * Canvas Editor - Excalidraw-ähnlicher Zeichen-Editor
 */

class CanvasEditor {
    constructor(config) {
        this.canvasId = config.id;
        this.canvasName = config.name;
        this.elements = config.elements || [];
        this.currentUser = config.currentUser;
        
        // State
        this.currentTool = 'select';
        this.isLocked = false;
        this.isDrawing = false;
        this.isPanning = false;
        this.selectedElement = null;
        this.startX = 0;
        this.startY = 0;
        this.currentX = 0;
        this.currentY = 0;
        
        // Transform
        this.zoom = 1;
        this.panX = 0;
        this.panY = 0;
        
        // History
        this.history = [];
        this.historyIndex = -1;
        this.maxHistorySize = 50;
        
        // DOM Elements
        this.svg = null;
        this.overlay = null;
        this.container = null;
        
        // SocketIO
        this.socket = null;
        this.activeUsers = new Map();
        
        // Text editing
        this.textInput = null;
        this.editingElement = null;
        
        // Debouncing für Speicherung während Verschieben
        this.saveTimeout = null;
        this.isDragging = false;
    }
    
    init() {
        this.setupDOM();
        this.setupEventListeners();
        this.setupSocketIO();
        this.loadElements();
        this.updateUI();
    }
    
    setupDOM() {
        this.svg = document.getElementById('canvas-svg');
        this.overlay = document.getElementById('canvas-overlay');
        this.container = document.querySelector('.canvas-area-container');
        
        if (!this.svg || !this.container) {
            console.error('Canvas DOM elements not found');
            return;
        }
        
        // Setze SVG ViewBox
        this.updateSVGViewBox();
    }
    
    setupEventListeners() {
        // Tool Buttons
        document.querySelectorAll('.canvas-tool-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tool = e.currentTarget.dataset.tool;
                this.setTool(tool);
            });
        });
        
        // Lock Button
        const lockBtn = document.querySelector('[data-tool="lock"]');
        if (lockBtn) {
            lockBtn.addEventListener('click', () => {
                this.toggleLock();
            });
        }
        
        // Zoom Controls
        document.getElementById('zoom-in')?.addEventListener('click', () => {
            this.zoomIn();
        });
        
        document.getElementById('zoom-out')?.addEventListener('click', () => {
            this.zoomOut();
        });
        
        // Undo/Redo
        document.getElementById('undo-btn')?.addEventListener('click', () => {
            this.undo();
        });
        
        document.getElementById('redo-btn')?.addEventListener('click', () => {
            this.redo();
        });
        
        // Canvas Events
        this.container.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.container.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.container.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.container.addEventListener('wheel', (e) => this.onWheel(e));
        
        // Bild-Upload
        const imageBtn = document.querySelector('[data-tool="image"]');
        const imageInput = document.getElementById('image-upload-input');
        
        if (imageBtn && imageInput) {
            imageBtn.addEventListener('click', () => {
                if (this.currentTool === 'image') {
                    imageInput.click();
                }
            });
            
            imageInput.addEventListener('change', (e) => {
                this.handleImageUpload(e);
            });
        }
        
        // Keyboard Shortcuts
        document.addEventListener('keydown', (e) => this.onKeyDown(e));
        document.addEventListener('keyup', (e) => this.onKeyUp(e));
    }
    
    setupSocketIO() {
        if (typeof io === 'undefined') {
            console.warn('SocketIO not loaded');
            return;
        }
        
        this.socket = io();
        
        // Join canvas room
        this.socket.emit('join_canvas', { canvas_id: this.canvasId, user: this.currentUser });
        
        // Listen for events
        this.socket.on('canvas:user_joined', (data) => {
            this.addActiveUser(data.user);
        });
        
        this.socket.on('canvas:user_left', (data) => {
            this.removeActiveUser(data.user_id);
        });
        
        this.socket.on('canvas:active_users', (data) => {
            data.users.forEach(user => this.addActiveUser(user));
        });
        
        this.socket.on('canvas:element_added', (data) => {
            if (data.user_id !== this.currentUser.id) {
                this.addElement(data.element);
            }
        });
        
        this.socket.on('canvas:element_updated', (data) => {
            if (data.user_id !== this.currentUser.id) {
                this.updateElement(data.element);
            }
        });
        
        this.socket.on('canvas:element_deleted', (data) => {
            if (data.user_id !== this.currentUser.id) {
                this.deleteElement(data.element_id);
            }
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
        });
    }
    
    setTool(tool) {
        if (this.isLocked && tool !== 'lock') {
            return;
        }
        
        this.currentTool = tool;
        this.container.setAttribute('data-tool', tool);
        
        // Update UI
        document.querySelectorAll('.canvas-tool-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-tool="${tool}"]`);
        if (activeBtn) {
            activeBtn.classList.add('active');
        }
        
        // Update cursor
        this.updateCursor();
    }
    
    toggleLock() {
        this.isLocked = !this.isLocked;
        const lockBtn = document.querySelector('[data-tool="lock"]');
        
        if (this.isLocked) {
            lockBtn.classList.add('active');
            lockBtn.querySelector('i').classList.remove('bi-lock');
            lockBtn.querySelector('i').classList.add('bi-lock-fill');
            this.setTool('lock');
        } else {
            lockBtn.classList.remove('active');
            lockBtn.querySelector('i').classList.remove('bi-lock-fill');
            lockBtn.querySelector('i').classList.add('bi-lock');
            this.setTool('select');
        }
    }
    
    updateCursor() {
        // Cursor wird über CSS gesteuert
    }
    
    onMouseDown(e) {
        if (this.isLocked) return;
        
        // Schließe Text-Input wenn außerhalb geklickt wird
        if (this.textInput && !this.textInput.contains(e.target)) {
            this.finishTextInput();
        }
        
        const rect = this.container.getBoundingClientRect();
        // Korrekte Koordinatenberechnung: ViewBox-Transformation berücksichtigen
        this.startX = (e.clientX - rect.left + this.panX) / this.zoom;
        this.startY = (e.clientY - rect.top + this.panY) / this.zoom;
        this.currentX = this.startX;
        this.currentY = this.startY;
        
        if (this.currentTool === 'hand' || (e.spaceKey && this.currentTool !== 'text')) {
            this.isPanning = true;
            this.container.style.cursor = 'grabbing';
            return;
        }
        
        if (this.currentTool === 'select') {
            // Prüfe ob Element angeklickt wurde
            const clickedElement = this.getElementAt(this.startX, this.startY);
            if (clickedElement) {
                // Entferne alte Original-Position falls vorhanden
                if (clickedElement._originalX !== undefined) {
                    delete clickedElement._originalX;
                    delete clickedElement._originalY;
                    if (clickedElement._originalCx !== undefined) {
                        delete clickedElement._originalCx;
                        delete clickedElement._originalCy;
                    }
                    if (clickedElement._originalX1 !== undefined) {
                        delete clickedElement._originalX1;
                        delete clickedElement._originalY1;
                        delete clickedElement._originalX2;
                        delete clickedElement._originalY2;
                    }
                }
                this.selectElement(clickedElement);
                this.isDrawing = true;
            } else {
                this.deselectElement();
            }
        } else if (this.currentTool === 'text') {
            // Prüfe ob Text-Element angeklickt wurde
            const clickedElement = this.getElementAt(this.startX, this.startY);
            if (clickedElement && clickedElement.type === 'text') {
                // Text bearbeiten
                this.editTextElement(clickedElement, this.startX, this.startY);
            } else {
                // Neuen Text erstellen
                this.createTextElement(this.startX, this.startY);
            }
        } else if (this.currentTool === 'eraser') {
            const element = this.getElementAt(this.startX, this.startY);
            if (element) {
                this.deleteElement(element.id);
            }
        } else if (['rectangle', 'diamond', 'circle', 'arrow', 'line'].includes(this.currentTool)) {
            this.isDrawing = true;
        }
    }
    
    onMouseMove(e) {
        const rect = this.container.getBoundingClientRect();
        // Korrekte Koordinatenberechnung: ViewBox-Transformation berücksichtigen
        this.currentX = (e.clientX - rect.left + this.panX) / this.zoom;
        this.currentY = (e.clientY - rect.top + this.panY) / this.zoom;
        
        if (this.isPanning) {
            const dx = e.movementX;
            const dy = e.movementY;
            this.panX += dx;
            this.panY += dy;
            this.updateSVGViewBox();
            return;
        }
        
        if (this.isDrawing) {
            if (this.currentTool === 'select' && this.selectedElement) {
                // Element verschieben - korrekte Delta-Berechnung
                const dx = this.currentX - this.startX;
                const dy = this.currentY - this.startY;
                
                // Nur verschieben wenn Bewegung groß genug (verhindert Zittern)
                if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
                    this.moveElement(this.selectedElement, dx, dy);
                    this.startX = this.currentX;
                    this.startY = this.currentY;
                }
            } else if (['rectangle', 'diamond', 'circle', 'arrow', 'line'].includes(this.currentTool)) {
                // Zeichnen
                this.drawPreview();
            }
        }
    }
    
    onMouseUp(e) {
        if (this.isPanning) {
            this.isPanning = false;
            this.container.style.cursor = '';
            return;
        }
        
        if (this.isDrawing && ['rectangle', 'diamond', 'circle', 'arrow', 'line'].includes(this.currentTool)) {
            this.finishDrawing();
        }
        
        // Finale Speicherung beim Loslassen
        if (this.isDragging && this.selectedElement) {
            if (this.saveTimeout) {
                clearTimeout(this.saveTimeout);
            }
            // Entferne temporäre Original-Position
            if (this.selectedElement._originalX !== undefined) {
                delete this.selectedElement._originalX;
                delete this.selectedElement._originalY;
                if (this.selectedElement._originalCx !== undefined) {
                    delete this.selectedElement._originalCx;
                    delete this.selectedElement._originalCy;
                }
                if (this.selectedElement._originalX1 !== undefined) {
                    delete this.selectedElement._originalX1;
                    delete this.selectedElement._originalY1;
                    delete this.selectedElement._originalX2;
                    delete this.selectedElement._originalY2;
                }
            }
            this.saveElement(this.selectedElement);
            this.isDragging = false;
        }
        
        this.isDrawing = false;
    }
    
    onWheel(e) {
        e.preventDefault();
        
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        const rect = this.container.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left - this.panX) / this.zoom;
        const mouseY = (e.clientY - rect.top - this.panY) / this.zoom;
        
        this.zoom *= delta;
        this.zoom = Math.max(0.1, Math.min(5, this.zoom));
        
        // Zoom zum Mauszeiger
        this.panX = e.clientX - rect.left - mouseX * this.zoom;
        this.panY = e.clientY - rect.top - mouseY * this.zoom;
        
        this.updateSVGViewBox();
        this.updateZoomUI();
    }
    
    onKeyDown(e) {
        if (e.code === 'Space') {
            e.preventDefault();
            e.spaceKey = true;
        }
        
        // Undo/Redo
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                this.undo();
            } else if (e.key === 'z' && e.shiftKey) {
                e.preventDefault();
                this.redo();
            } else if (e.key === 'y') {
                e.preventDefault();
                this.redo();
            }
        }
    }
    
    onKeyUp(e) {
        if (e.code === 'Space') {
            e.spaceKey = false;
        }
    }
    
    updateSVGViewBox() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        // ViewBox mit korrekter Transformation
        // panX und panY sind bereits in Pixel-Koordinaten, müssen durch zoom geteilt werden
        this.svg.setAttribute('viewBox', `${-this.panX / this.zoom} ${-this.panY / this.zoom} ${width / this.zoom} ${height / this.zoom}`);
    }
    
    drawPreview() {
        // Entferne vorherige Preview
        const preview = this.svg.querySelector('.drawing-preview');
        if (preview) {
            preview.remove();
        }
        
        const width = Math.abs(this.currentX - this.startX);
        const height = Math.abs(this.currentY - this.startY);
        const x = Math.min(this.startX, this.currentX);
        const y = Math.min(this.startY, this.currentY);
        
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.classList.add('drawing-preview');
        
        let element;
        
        switch (this.currentTool) {
            case 'rectangle':
                element = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                element.setAttribute('x', x);
                element.setAttribute('y', y);
                element.setAttribute('width', width);
                element.setAttribute('height', height);
                break;
                
            case 'circle':
                const radius = Math.sqrt(width * width + height * height) / 2;
                element = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                element.setAttribute('cx', this.startX);
                element.setAttribute('cy', this.startY);
                element.setAttribute('r', radius);
                break;
                
            case 'diamond':
                const points = [
                    `${this.startX + width / 2},${y}`,
                    `${x + width},${this.startY + height / 2}`,
                    `${this.startX + width / 2},${y + height}`,
                    `${x},${this.startY + height / 2}`
                ].join(' ');
                element = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                element.setAttribute('points', points);
                break;
                
            case 'line':
                element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                element.setAttribute('x1', this.startX);
                element.setAttribute('y1', this.startY);
                element.setAttribute('x2', this.currentX);
                element.setAttribute('y2', this.currentY);
                break;
                
            case 'arrow':
                element = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                element.setAttribute('x1', this.startX);
                element.setAttribute('y1', this.startY);
                element.setAttribute('x2', this.currentX);
                element.setAttribute('y2', this.currentY);
                element.setAttribute('marker-end', 'url(#arrowhead)');
                break;
        }
        
        if (element) {
            element.setAttribute('stroke', '#000000');
            element.setAttribute('stroke-width', '2');
            element.setAttribute('fill', 'none');
            g.appendChild(element);
            this.svg.appendChild(g);
        }
    }
    
    finishDrawing() {
        const preview = this.svg.querySelector('.drawing-preview');
        if (!preview) return;
        
        const width = Math.abs(this.currentX - this.startX);
        const height = Math.abs(this.currentY - this.startY);
        const x = Math.min(this.startX, this.currentX);
        const y = Math.min(this.startY, this.currentY);
        
        const properties = {
            x: x,
            y: y,
            width: width,
            height: height,
            strokeColor: '#000000',
            fillColor: 'none',
            strokeWidth: 2
        };
        
        if (this.currentTool === 'circle') {
            properties.cx = this.startX;
            properties.cy = this.startY;
            properties.r = Math.sqrt(width * width + height * height) / 2;
        } else if (this.currentTool === 'diamond') {
            properties.points = [
                { x: this.startX + width / 2, y: y },
                { x: x + width, y: this.startY + height / 2 },
                { x: this.startX + width / 2, y: y + height },
                { x: x, y: this.startY + height / 2 }
            ];
        } else if (this.currentTool === 'line' || this.currentTool === 'arrow') {
            properties.x1 = this.startX;
            properties.y1 = this.startY;
            properties.x2 = this.currentX;
            properties.y2 = this.currentY;
        }
        
        preview.remove();
        
        this.createElement(this.currentTool, properties);
    }
    
    createElement(type, properties) {
        const element = {
            id: Date.now(),
            type: type,
            properties: properties,
            z_index: this.elements.length
        };
        
        this.addElement(element);
        this.saveElement(element);
        this.addToHistory();
    }
    
    createTextElement(x, y, existingText = '') {
        // Entferne vorhandenes Text-Input falls vorhanden
        this.closeTextInput();
        
        // Erstelle Text-Input-Element
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'canvas-text-input';
        input.value = existingText;
        input.style.position = 'absolute';
        input.style.left = '0';
        input.style.top = '0';
        input.style.border = 'none';
        input.style.outline = 'none';
        input.style.background = 'transparent';
        input.style.fontSize = '16px';
        input.style.color = '#000000';
        input.style.padding = '2px 4px';
        input.style.minWidth = '100px';
        input.style.fontFamily = 'inherit';
        
        // Position berechnen (SVG-Koordinaten zu Pixel-Koordinaten)
        const rect = this.container.getBoundingClientRect();
        // Korrekte Transformation: ViewBox berücksichtigen
        const pixelX = rect.left + (x * this.zoom) - this.panX;
        const pixelY = rect.top + (y * this.zoom) - this.panY;
        
        input.style.left = pixelX + 'px';
        input.style.top = pixelY + 'px';
        
        this.overlay.appendChild(input);
        this.textInput = input;
        this.editingElement = null;
        
        // Focus und Select
        input.focus();
        input.select();
        
        // Event-Handler
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.finishTextInput();
            } else if (e.key === 'Escape') {
                e.preventDefault();
                this.closeTextInput();
            }
        });
        
        input.addEventListener('blur', () => {
            // Delay um Click-Events zu ermöglichen
            setTimeout(() => {
                if (this.textInput === input) {
                    this.finishTextInput();
                }
            }, 200);
        });
    }
    
    editTextElement(element, x, y) {
        const props = element.properties;
        this.editingElement = element;
        this.createTextElement(x, y, props.text || '');
    }
    
    finishTextInput() {
        if (!this.textInput) return;
        
        const text = this.textInput.value.trim();
        
        if (this.editingElement) {
            // Text bearbeiten
            if (text) {
                this.editingElement.properties.text = text;
                this.renderElement(this.editingElement);
                this.saveElement(this.editingElement);
                this.addToHistory();
            } else {
                // Text löschen wenn leer
                this.deleteElement(this.editingElement.id);
            }
            this.editingElement = null;
        } else if (text) {
            // Neuen Text erstellen
            const rect = this.container.getBoundingClientRect();
            const inputRect = this.textInput.getBoundingClientRect();
            // Korrekte Rücktransformation
            const x = (inputRect.left - rect.left + this.panX) / this.zoom;
            const y = (inputRect.top - rect.top + this.panY) / this.zoom;
            
            const properties = {
                x: x,
                y: y,
                text: text,
                fontSize: 16,
                color: '#000000'
            };
            
            this.createElement('text', properties);
        }
        
        this.closeTextInput();
    }
    
    closeTextInput() {
        if (this.textInput) {
            this.textInput.remove();
            this.textInput = null;
        }
        this.editingElement = null;
    }
    
    addElement(element) {
        this.elements.push(element);
        this.renderElement(element);
    }
    
    updateElement(element) {
        const index = this.elements.findIndex(e => e.id === element.id);
        if (index !== -1) {
            this.elements[index] = element;
            this.renderElement(element);
        }
    }
    
    deleteElement(elementId) {
        this.elements = this.elements.filter(e => e.id !== elementId);
        const svgElement = this.svg.querySelector(`[data-element-id="${elementId}"]`);
        if (svgElement) {
            svgElement.remove();
        }
    }
    
    moveElement(element, dx, dy) {
        const props = element.properties;
        
        // Speichere ursprüngliche Position beim ersten Verschieben
        if (!element._originalX) {
            element._originalX = props.x;
            element._originalY = props.y;
            if (props.cx !== undefined) {
                element._originalCx = props.cx;
                element._originalCy = props.cy;
            }
            if (props.x1 !== undefined) {
                element._originalX1 = props.x1;
                element._originalY1 = props.y1;
                element._originalX2 = props.x2;
                element._originalY2 = props.y2;
            }
        }
        
        // Berechne neue absolute Position
        props.x = element._originalX + dx;
        props.y = element._originalY + dy;
        
        if (props.cx !== undefined) {
            props.cx = element._originalCx + dx;
            props.cy = element._originalCy + dy;
        }
        
        if (props.x1 !== undefined) {
            props.x1 = element._originalX1 + dx;
            props.y1 = element._originalY1 + dy;
            props.x2 = element._originalX2 + dx;
            props.y2 = element._originalY2 + dy;
        }
        
        // Rendere Element (entfernt automatisch alte Version)
        this.renderElement(element);
        
        // Debounce Speicherung während Verschieben
        this.isDragging = true;
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        this.saveTimeout = setTimeout(() => {
            this.saveElement(element);
            this.isDragging = false;
        }, 150); // Speichere nach 150ms Pause
    }
    
    renderElement(element) {
        // Entferne ALLE vorhandenen Elemente mit dieser ID (verhindert Duplikate)
        const existing = this.svg.querySelectorAll(`[data-element-id="${element.id}"]`);
        existing.forEach(el => el.remove());
        
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.setAttribute('data-element-id', element.id);
        g.classList.add('canvas-element');
        
        if (this.selectedElement && this.selectedElement.id === element.id) {
            g.classList.add('selected');
        }
        
        const props = element.properties;
        let svgElement;
        
        switch (element.type) {
            case 'rectangle':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                svgElement.setAttribute('x', props.x);
                svgElement.setAttribute('y', props.y);
                svgElement.setAttribute('width', props.width);
                svgElement.setAttribute('height', props.height);
                break;
                
            case 'circle':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                svgElement.setAttribute('cx', props.cx || props.x);
                svgElement.setAttribute('cy', props.cy || props.y);
                svgElement.setAttribute('r', props.r || Math.min(props.width, props.height) / 2);
                break;
                
            case 'diamond':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
                const points = props.points ? 
                    props.points.map(p => `${p.x},${p.y}`).join(' ') :
                    `${props.x + props.width / 2},${props.y} ${props.x + props.width},${props.y + props.height / 2} ${props.x + props.width / 2},${props.y + props.height} ${props.x},${props.y + props.height / 2}`;
                svgElement.setAttribute('points', points);
                break;
                
            case 'line':
            case 'arrow':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                svgElement.setAttribute('x1', props.x1 || props.x);
                svgElement.setAttribute('y1', props.y1 || props.y);
                svgElement.setAttribute('x2', props.x2 || (props.x + props.width));
                svgElement.setAttribute('y2', props.y2 || (props.y + props.height));
                if (element.type === 'arrow') {
                    svgElement.setAttribute('marker-end', 'url(#arrowhead)');
                }
                break;
                
            case 'text':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                svgElement.setAttribute('x', props.x);
                svgElement.setAttribute('y', props.y);
                svgElement.setAttribute('font-size', props.fontSize || 16);
                svgElement.setAttribute('fill', props.color || '#000000');
                svgElement.textContent = props.text || '';
                break;
                
            case 'image':
                svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'image');
                svgElement.setAttribute('x', props.x);
                svgElement.setAttribute('y', props.y);
                svgElement.setAttribute('width', props.width);
                svgElement.setAttribute('height', props.height);
                svgElement.setAttribute('href', props.imageUrl);
                break;
        }
        
        if (svgElement) {
            if (element.type !== 'text' && element.type !== 'image') {
                svgElement.setAttribute('stroke', props.strokeColor || '#000000');
                svgElement.setAttribute('stroke-width', props.strokeWidth || 2);
                svgElement.setAttribute('fill', props.fillColor || 'none');
            }
            
            g.appendChild(svgElement);
            this.svg.appendChild(g);
        }
    }
    
    loadElements() {
        // Erstelle Arrow Marker
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
        marker.setAttribute('id', 'arrowhead');
        marker.setAttribute('markerWidth', '10');
        marker.setAttribute('markerHeight', '10');
        marker.setAttribute('refX', '9');
        marker.setAttribute('refY', '3');
        marker.setAttribute('orient', 'auto');
        
        const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
        polygon.setAttribute('points', '0 0, 10 3, 0 6');
        polygon.setAttribute('fill', '#000000');
        marker.appendChild(polygon);
        defs.appendChild(marker);
        this.svg.appendChild(defs);
        
        // Lade Elemente
        this.elements.forEach(element => {
            this.renderElement(element);
        });
    }
    
    getElementAt(x, y) {
        // Verbessertes Hit-Testing für alle Elementtypen
        for (let i = this.elements.length - 1; i >= 0; i--) {
            const element = this.elements[i];
            const props = element.properties;
            
            if (element.type === 'rectangle' || element.type === 'image') {
                if (x >= props.x && x <= props.x + props.width &&
                    y >= props.y && y <= props.y + props.height) {
                    return element;
                }
            } else if (element.type === 'circle') {
                const cx = props.cx || props.x;
                const cy = props.cy || props.y;
                const r = props.r || Math.min(props.width, props.height) / 2;
                const dist = Math.sqrt((x - cx) ** 2 + (y - cy) ** 2);
                if (dist <= r) {
                    return element;
                }
            } else if (element.type === 'diamond') {
                // Hit-Test für Diamant (Polygon)
                const points = props.points || [
                    { x: props.x + props.width / 2, y: props.y },
                    { x: props.x + props.width, y: props.y + props.height / 2 },
                    { x: props.x + props.width / 2, y: props.y + props.height },
                    { x: props.x, y: props.y + props.height / 2 }
                ];
                if (this.pointInPolygon(x, y, points)) {
                    return element;
                }
            } else if (element.type === 'line' || element.type === 'arrow') {
                // Hit-Test für Linie (mit Toleranz)
                const x1 = props.x1 || props.x;
                const y1 = props.y1 || props.y;
                const x2 = props.x2 || (props.x + props.width);
                const y2 = props.y2 || (props.y + props.height);
                const dist = this.distanceToLine(x, y, x1, y1, x2, y2);
                if (dist < 5) { // 5 Pixel Toleranz
                    return element;
                }
            } else if (element.type === 'text') {
                // Hit-Test für Text (ungefährer Bereich)
                const fontSize = props.fontSize || 16;
                const textWidth = (props.text || '').length * fontSize * 0.6; // Grobe Schätzung
                const textHeight = fontSize;
                if (x >= props.x && x <= props.x + textWidth &&
                    y >= props.y - textHeight && y <= props.y) {
                    return element;
                }
            }
        }
        return null;
    }
    
    pointInPolygon(x, y, points) {
        let inside = false;
        for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
            const xi = points[i].x, yi = points[i].y;
            const xj = points[j].x, yj = points[j].y;
            const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) inside = !inside;
        }
        return inside;
    }
    
    distanceToLine(px, py, x1, y1, x2, y2) {
        const A = px - x1;
        const B = py - y1;
        const C = x2 - x1;
        const D = y2 - y1;
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        if (lenSq !== 0) param = dot / lenSq;
        let xx, yy;
        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }
        const dx = px - xx;
        const dy = py - yy;
        return Math.sqrt(dx * dx + dy * dy);
    }
    
    selectElement(element) {
        this.selectedElement = element;
        this.renderElement(element);
    }
    
    deselectElement() {
        if (this.selectedElement) {
            const svgElement = this.svg.querySelector(`[data-element-id="${this.selectedElement.id}"]`);
            if (svgElement) {
                svgElement.classList.remove('selected');
            }
        }
        this.selectedElement = null;
    }
    
    zoomIn() {
        this.zoom *= 1.2;
        this.zoom = Math.min(5, this.zoom);
        this.updateSVGViewBox();
        this.updateZoomUI();
    }
    
    zoomOut() {
        this.zoom *= 0.8;
        this.zoom = Math.max(0.1, this.zoom);
        this.updateSVGViewBox();
        this.updateZoomUI();
    }
    
    updateZoomUI() {
        const zoomLevel = document.getElementById('zoom-level');
        if (zoomLevel) {
            zoomLevel.textContent = Math.round(this.zoom * 100) + '%';
        }
    }
    
    addToHistory() {
        // Entferne Zukunft wenn neue Aktion
        this.history = this.history.slice(0, this.historyIndex + 1);
        
        // Füge aktuellen State hinzu
        this.history.push(JSON.parse(JSON.stringify(this.elements)));
        
        // Begrenze History-Größe
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        } else {
            this.historyIndex++;
        }
        
        this.updateHistoryUI();
    }
    
    undo() {
        if (this.historyIndex > 0) {
            this.historyIndex--;
            this.elements = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.reloadElements();
            this.updateHistoryUI();
        }
    }
    
    redo() {
        if (this.historyIndex < this.history.length - 1) {
            this.historyIndex++;
            this.elements = JSON.parse(JSON.stringify(this.history[this.historyIndex]));
            this.reloadElements();
            this.updateHistoryUI();
        }
    }
    
    reloadElements() {
        // Entferne alle Elemente
        this.svg.querySelectorAll('.canvas-element').forEach(el => el.remove());
        
        // Rendere neu
        this.loadElements();
    }
    
    updateHistoryUI() {
        const undoBtn = document.getElementById('undo-btn');
        const redoBtn = document.getElementById('redo-btn');
        
        if (undoBtn) {
            undoBtn.disabled = this.historyIndex <= 0;
        }
        
        if (redoBtn) {
            redoBtn.disabled = this.historyIndex >= this.history.length - 1;
        }
    }
    
    updateUI() {
        this.updateZoomUI();
        this.updateHistoryUI();
    }
    
    async saveElement(element) {
        // Überspringe Speicherung wenn Element noch keine ID hat (wird beim ersten Speichern erstellt)
        if (!element.id) {
            // Neues Element erstellen
            try {
                const response = await fetch(`/canvas/${this.canvasId}/element`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        element_type: element.type,
                        properties: element.properties,
                        z_index: element.z_index
                    })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    element.id = data.id;
                    
                    // Broadcast über SocketIO
                    if (this.socket) {
                        this.socket.emit('canvas:element_added', {
                            canvas_id: this.canvasId,
                            element: element
                        });
                    }
                }
            } catch (error) {
                console.error('Error saving element:', error);
            }
        } else {
            // Bestehendes Element aktualisieren (nicht neu erstellen!)
            try {
                const response = await fetch(`/canvas/element/${element.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        properties: element.properties,
                        z_index: element.z_index
                    })
                });
                
                if (response.ok) {
                    // Broadcast über SocketIO
                    if (this.socket) {
                        this.socket.emit('canvas:element_updated', {
                            canvas_id: this.canvasId,
                            element: element
                        });
                    }
                }
            } catch (error) {
                console.error('Error updating element:', error);
            }
        }
    }
    
    async handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('image', file);
        formData.append('canvas_id', this.canvasId);
        
        try {
            const response = await fetch(`/canvas/${this.canvasId}/upload-image`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                
                const properties = {
                    x: this.startX,
                    y: this.startY,
                    width: data.width || 200,
                    height: data.height || 200,
                    imageUrl: data.url
                };
                
                this.createElement('image', properties);
            }
        } catch (error) {
            console.error('Error uploading image:', error);
        }
        
        // Reset input
        e.target.value = '';
    }
    
    addActiveUser(user) {
        if (user.id === this.currentUser.id) return;
        
        this.activeUsers.set(user.id, user);
        this.renderActiveUsers();
    }
    
    removeActiveUser(userId) {
        this.activeUsers.delete(userId);
        this.renderActiveUsers();
    }
    
    renderActiveUsers() {
        const container = document.getElementById('canvas-active-users');
        if (!container) return;
        
        container.innerHTML = '';
        
        this.activeUsers.forEach(user => {
            const avatar = document.createElement('div');
            avatar.className = 'canvas-user-avatar';
            avatar.title = user.name;
            
            if (user.profilePicture) {
                const img = document.createElement('img');
                img.src = `/settings/profile-picture/${user.profilePicture}`;
                img.alt = user.name;
                avatar.appendChild(img);
            } else {
                const initial = document.createElement('div');
                initial.className = 'avatar-initial';
                initial.textContent = user.name.charAt(0).toUpperCase();
                avatar.appendChild(initial);
            }
            
            container.appendChild(avatar);
        });
    }
}

