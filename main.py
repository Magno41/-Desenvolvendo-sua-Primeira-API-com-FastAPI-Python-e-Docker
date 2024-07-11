## Instalação das Dependências
pip install fastapi sqlalchemy fastapi-pagination uvicorn 

# Importação dos módulos necessários do SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# Definição da classe Atleta, que representa a tabela 'atletas' no banco de dados
class Atleta(Base):
    __tablename__ = "atletas"  # Nome da tabela

    # Definição das colunas da tabela
    id = Column(Integer, primary_key=True, autoincrement=True)  # Coluna 'id' como chave primária com auto incremento
    nome = Column(String(255), nullable=False)  # Coluna 'nome' do tipo String, não pode ser nula
    cpf = Column(String(11), unique=True, nullable=False)  # Coluna 'cpf' do tipo String, deve ser única e não pode ser nula
    centro_treinamento = Column(String(255))  # Coluna 'centro_treinamento' do tipo String, pode ser nula
    categoria = Column(String(255))  # Coluna 'categoria' do tipo String, pode ser nula

    # Relacionamento com tabela de treinos (opcional)
    # treinos = relationship("Treino", backref="atleta")

# Configuração do Banco de Dados:
# Importação dos módulos necessários do SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

# URL de conexão com o banco de dados
DATABASE_URL = "postgresql://user:password@host:port/database"

# Criação do engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Criação de todas as tabelas definidas em classes que herdam de Base
Base.metadata.create_all(engine)

# Configuração da sessão do SQLAlchemy
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Implementação da API Assíncrona com FastAPI
# Importação dos módulos necessários do FastAPI e SQLAlchemy
from fastapi import FastAPI, Depends, HTTPException
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from models import Atleta
from database import SessionLocal

# Criação da instância do FastAPI
app = FastAPI()

# Evento que ocorre ao iniciar a aplicação
@app.on_event("startup")
async def startup_event():
    global session
    session = SessionLocal()  # Cria uma sessão global

# Evento que ocorre ao finalizar a aplicação
@app.on_event("shutdown")
async def shutdown_event():
    global session
    session.close()  # Fecha a sessão global

# Função que fornece uma sessão do banco de dados para as rotas da API
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Definição dos modelos Pydantic para validação e serialização de dados
class AtletaBase(BaseModel):
    nome: str
    cpf: str
    centro_treinamento: str | None = None
    categoria: str | None = None

class AtletaCreate(AtletaBase):
    pass

class AtletaResponse(AtletaBase):
    id: int

    class Config:
        orm_mode = True  # Permite a conversão do modelo ORM para modelo Pydantic

# Endpoint para buscar todos os atletas com paginação
@app.get("/atletas", response_model=Page[AtletaResponse])
async def get_all_atletas(db: Session = Depends(get_db), limit: int | None = None, offset: int | None = None):
    query = db.query(Atleta).order_by(Atleta.id)  # Consulta todos os atletas ordenados pelo 'id'
    return paginate(query)  # Retorna a consulta paginada

# Endpoint para buscar atletas por nome e CPF
@app.get("/atletas/search", response_model=List[AtletaResponse])
async def get_atleta_by_nome_cpf(nome: str | None = None, cpf: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Atleta)  # Inicia a consulta na tabela 'atletas'

    if nome:
        query = query.filter(Atleta.nome.ilike(f"%{nome}%"))  # Filtra por nome se fornecido

    if cpf:
        query = query.filter(Atleta.cpf == cpf)  # Filtra por CPF se fornecido

    atletas = query.all()  # Executa a consulta

    if not atletas:
        raise HTTPException(status_code=404, detail="Atleta não encontrado")  # Lança exceção se nenhum atleta for encontrado

    return atletas  # Retorna a lista de atletas encontrados

# Endpoint para cadastrar um novo atleta
@app.post("/atletas", response_model=AtletaResponse)
async def create_atleta(atleta: AtletaCreate, db: Session = Depends(get_db)):
    db_atleta = Atleta(**atleta.dict())  # Cria uma instância do modelo Atleta
    db.add(db_atleta)  # Adiciona a instância ao banco de dados
    db.commit()  # Confirma a transação
    db.refresh(db_atleta)  # Atualiza a instância com dados do banco de dados
    return db_atleta  # Retorna o novo atleta criado

# Adiciona a funcionalidade de paginação à aplicação
add_pagination(app)
