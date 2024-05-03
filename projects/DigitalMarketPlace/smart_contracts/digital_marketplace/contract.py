from algopy import *


class DigitalMarketplace(ARC4Contract):
    # Declaro variables en el global state
    # Local state es un dato relacionado a una cuenta específica
    # Global state es un dato que se ejecutan en el contrato con todas las
    # cuentas que estén interactuando
    asset_id: UInt64
    unitary_price: UInt64
    # Create the app
    @arc4.abimethod(allow_actions=["NoOp"], create="require") # decorador para que el método sea llamable por otros clientes
    def create_application(self, asset_id: Asset, unitary_price: UInt64) -> None:
        # Guardar un numero de asset ID
        self.asset_id = asset_id.id
        # Guardar un precio unitario
        self.unitary_price = unitary_price
    
    # Hacer que el contrato haga opt in al asset
    @arc4.abimethod
    def opt_in_to_asset(self, mbr_pay: gtxn.PaymentTransaction) -> None:
        # Quien invoca este método debe ser el mismo que creó el contrato
        assert Txn.sender == Global.creator_address
        assert not Global.current_application_address.is_opted_in(Asset(self.asset_id))
        # Se verifica que se mande una transacción de pago a la cuenta de contrato
        assert mbr_pay.receiver == Global.current_application_address
        # 
        assert mbr_pay.amount == Global.min_balance + Global.asset_opt_in_min_balance
        
        
        # Creamos una inner transaction
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver= Global.current_application_address,
            asset_amount=0,
        ).submit()
    # opt in (spam prevention feature) the asset that will be sold
    # El usuario enviará los assets, el contrato para poder recibirlos
    # debe hacer un permiso
    
    # Usuario vendedor defina el precio de venta de los assets
    @arc4.abimethod
    def set_price(self, unitary_price: UInt64) -> None:
        assert Txn.sender == Global.creator_address
        
        self.unitary_price = unitary_price
    
    # Usuario comprador puede hacer la compra de n assets
    @arc4.abimethod
    def buy(
        self,
        quantity: UInt64,
        buyer_txn: gtxn.PaymentTransaction
    ) -> None:
        assert self.unitary_price != UInt64(0)
        assert buyer_txn.sender == Txn.sender
        assert buyer_txn.receiver == Global.current_application_address
        assert buyer_txn.amount == self.unitary_price *quantity
        
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_receiver=Txn.sender,asset_amount=quantity
        ).submit()
        
    
    # Usuario vendedor pueda reclamar las ganancias y assets sobrantes
    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def delete_application(self) -> None:
        # Se verifica que el unico que elimine la aplicacion sea el creador
        
        assert Txn.sender == Global.creator_address
        # Reclamar el saldo de los productos
        itxn.AssetTransfer(
            xfer_asset=self.asset_id, # Envie los assets que le quedan al creador
            asset_receiver=Global.creator_address,
            asset_amount=0, # saca todo el saldo de la cuenta y lo envia a la cuenta del creador
            asset_close_to=Global.creator_address,
        ).submit()
        
        # Reclamar las ganancias de algos
        itxn.Payment(
            receiver=Global.creator_address,
            amount=0,
            close_remainder_to=Global.creator_address,
        ).submit()
    
    # Delete the application
