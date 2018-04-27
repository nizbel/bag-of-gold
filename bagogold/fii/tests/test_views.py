

class DetalharFIITestCase (TestCase):
    def setUp():
        # TODO Criar empresa
        # TODO Criar 2 FII
        # TODO Criar histórico de preços para 1
        # TODO Criar proventos para 1
        # TODO Criar agrupamento para 1
    
    def test_usuario_deslogado_fii_vazio:
        """Testa o acesso a view para um fii sem infos com um usuário deslogado"""
        # TODO acessar a view
        
        self.assertEqual(status_code, 200)
        
    def test_usuario_logado_fii_vazio:
        """Testa o acesso a view para um fii sem infos com um usuário logado"""
        # TODO Criar usuário
        
        # TODO Criar operações
        
        # TODO logar usuário
        
        self.assertEqual(status_code, 200)
        
        # TODO Verificar contexto
        
    def test_usuario_deslogado_fii_com_infos:
        """Testa o acesso a view para um fii com infos com um usuário deslogado"""
        # TODO acessar a view
        
        self.assertEqual(status_code, 200)
        
    def test_usuario_logado_fii_com_infos:
        """Testa o acesso a view para um fii com infos com um usuário logado"""
        # TODO Criar usuário
        
        # TODO Criar operações
        
        # TODO logar usuário
        
        self.assertEqual(status_code, 200)
        
        # TODO Verificar contexto