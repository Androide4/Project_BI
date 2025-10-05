-- Create and use the database

USE mydb;

-- Table for storing enrollment information
CREATE TABLE IF NOT EXISTS matricula (
    id_matricula INT NOT NULL AUTO_INCREMENT,
    costo DECIMAL NOT NULL,
    fecha_pago DATETIME NOT NULL,
    PRIMARY KEY (id_matricula)
) ENGINE = InnoDB;

-- Table for storing campus/location information
CREATE TABLE IF NOT EXISTS sede (
    id_sede INT NOT NULL AUTO_INCREMENT,
    nombre_sede VARCHAR(100) NOT NULL,
    ubicacion VARCHAR(45) NOT NULL,
    PRIMARY KEY (id_sede)
) ENGINE = InnoDB;

-- Table for storing student information
CREATE TABLE IF NOT EXISTS alumno (
    id_alumno INT NOT NULL AUTO_INCREMENT,
    nombre_alumno VARCHAR(45) NOT NULL,
    matricula_id INT NOT NULL,
    sede_id INT NOT NULL,
    PRIMARY KEY (id_alumno),
    INDEX idx_alumno_matricula (matricula_id),
    INDEX idx_alumno_sede (sede_id),
    CONSTRAINT fk_alumno_matricula
        FOREIGN KEY (matricula_id)
        REFERENCES matricula (id_matricula)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT fk_alumno_sede
        FOREIGN KEY (sede_id)
        REFERENCES sede (id_sede)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- Table for storing teacher information
CREATE TABLE IF NOT EXISTS docente (
    id_docente INT NOT NULL AUTO_INCREMENT,
    nombre_docente VARCHAR(45) NOT NULL,
    PRIMARY KEY (id_docente)
) ENGINE = InnoDB;

-- Table for storing class information
CREATE TABLE IF NOT EXISTS clase (
    id_clase INT NOT NULL AUTO_INCREMENT,
    nombre_clase VARCHAR(45) NOT NULL,
    docente_id INT NOT NULL,
    PRIMARY KEY (id_clase),
    INDEX idx_clase_docente (docente_id),
    CONSTRAINT fk_clase_docente
        FOREIGN KEY (docente_id)
        REFERENCES docente (id_docente)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- Table for storing payment information
CREATE TABLE IF NOT EXISTS pago (
    id_pago INT NOT NULL AUTO_INCREMENT,
    fecha DATETIME NOT NULL,
    valor_pago DECIMAL NOT NULL,
    periodo VARCHAR(7) NOT NULL,
    alumno_id INT NOT NULL,
    PRIMARY KEY (id_pago),
    INDEX idx_pago_alumno (alumno_id),
    CONSTRAINT fk_pago_alumno
        FOREIGN KEY (alumno_id)
        REFERENCES alumno (id_alumno)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- Table for storing attendance records
CREATE TABLE IF NOT EXISTS asistencia (
    id_asistencia INT NOT NULL AUTO_INCREMENT,
    fecha DATETIME NOT NULL,
    alumno_id INT NOT NULL,
    clase_id INT NOT NULL,
    sede_id INT NOT NULL,
    PRIMARY KEY (id_asistencia),
    INDEX idx_asistencia_alumno (alumno_id),
    INDEX idx_asistencia_clase (clase_id),
    INDEX idx_asistencia_sede (sede_id),
    CONSTRAINT fk_asistencia_alumno
        FOREIGN KEY (alumno_id)
        REFERENCES alumno (id_alumno)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT fk_asistencia_clase
        FOREIGN KEY (clase_id)
        REFERENCES clase (id_clase)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT fk_asistencia_sede
        FOREIGN KEY (sede_id)
        REFERENCES sede (id_sede)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE = InnoDB;

-- Junction table for class and campus relationships
CREATE TABLE IF NOT EXISTS clase_has_sede (
    clase_id INT NOT NULL,
    sede_id INT NOT NULL,
    PRIMARY KEY (clase_id, sede_id),
    INDEX idx_clase_has_sede_clase (clase_id),
    INDEX idx_clase_has_sede_sede (sede_id),
    CONSTRAINT fk_clase_has_sede_clase
        FOREIGN KEY (clase_id)
        REFERENCES clase (id_clase)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION,
    CONSTRAINT fk_clase_has_sede_sede
        FOREIGN KEY (sede_id)
        REFERENCES sede (id_sede)
        ON DELETE NO ACTION
        ON UPDATE NO ACTION
) ENGINE = InnoDB;


