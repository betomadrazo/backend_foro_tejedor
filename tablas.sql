CREATE TABLE eventos_streaming (
  id SERIAL PRIMARY KEY,
  nombre_evento VARCHAR(200),
  id_evento VARCHAR (255) UNIQUE,
  link_streaming VARCHAR(500),
  precio DOUBLE PRECISION,
  fecha_evento DATE DEFAULT CURRENT_TIMESTAMP,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  al_aire BOOLEAN DEFAULT FALSE
);

CREATE TABLE boletos_streaming (
  id SERIAL PRIMARY KEY,
  comprador VARCHAR(50),
  email VARCHAR(50),
  numero_boleto VARCHAR(100),
  asiento SMALLINT,
  activo BOOLEAN DEFAULT FALSE,
  fecha_evento DATE DEFAULT CURRENT_TIMESTAMP,
  fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  id_evento VARCHAR(255),
  recibio_boletos BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (id_evento) REFERENCES eventos_streaming(id_evento) ON DELETE CASCADE
);
