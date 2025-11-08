from datetime import datetime
from app import db
import json


class Canvas(db.Model):
    __tablename__ = 'canvases'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    text_fields = db.relationship('CanvasTextField', back_populates='canvas', cascade='all, delete-orphan')
    elements = db.relationship('CanvasElement', back_populates='canvas', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Canvas {self.name}>'


class CanvasTextField(db.Model):
    __tablename__ = 'canvas_text_fields'
    
    id = db.Column(db.Integer, primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvases.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    
    # Position and size
    pos_x = db.Column(db.Integer, default=0, nullable=False)
    pos_y = db.Column(db.Integer, default=0, nullable=False)
    width = db.Column(db.Integer, default=200, nullable=False)
    height = db.Column(db.Integer, default=100, nullable=False)
    
    # Styling
    font_size = db.Column(db.Integer, default=14)
    color = db.Column(db.String(7), default='#000000')
    background_color = db.Column(db.String(7), default='#ffffff')
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    canvas = db.relationship('Canvas', back_populates='text_fields')
    
    def __repr__(self):
        return f'<CanvasTextField {self.id} on canvas {self.canvas_id}>'


class CanvasElement(db.Model):
    __tablename__ = 'canvas_elements'
    
    id = db.Column(db.Integer, primary_key=True)
    canvas_id = db.Column(db.Integer, db.ForeignKey('canvases.id'), nullable=False)
    
    # Element type: rectangle, diamond, circle, arrow, line, text, image
    element_type = db.Column(db.String(50), nullable=False)
    
    # JSON-basierte Speicherung aller Eigenschaften
    properties = db.Column(db.Text, nullable=False)  # JSON string
    
    # Z-Index für Layering
    z_index = db.Column(db.Integer, default=0, nullable=False)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    canvas = db.relationship('Canvas', back_populates='elements')
    
    def get_properties(self):
        """Gibt die Properties als Dictionary zurück."""
        if self.properties:
            return json.loads(self.properties)
        return {}
    
    def set_properties(self, props_dict):
        """Setzt die Properties aus einem Dictionary."""
        self.properties = json.dumps(props_dict)
    
    def __repr__(self):
        return f'<CanvasElement {self.id} ({self.element_type}) on canvas {self.canvas_id}>'



