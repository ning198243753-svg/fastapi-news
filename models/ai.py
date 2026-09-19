from datetime import datetime                                                                                                            
                                                                                                                                            
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, func                                                                  
from sqlalchemy.orm import Mapped, mapped_column                                                                                         
                                                                                                                                            
from .base import Base                                                                                                                   
                                                                                                                                            
                                                                                                                                            
class AIChat(Base):                                                                                                          
       __tablename__ = "ai_chat"                                                                                                            
                                                                                                                                            
       id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)                                                       
       user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)                                                 
       message: Mapped[str] = mapped_column(Text, nullable=False)      # 用户问的                                                           
       response: Mapped[str] = mapped_column(Text, nullable=False)     # AI 答的                                                            
       created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, insert_default=func.now())                                    
                                                                                                                                            
       __table_args__ = (                                                                                                                   
           Index("idx_ai_chat_user_id", "user_id"),                                                                                         
       )                     