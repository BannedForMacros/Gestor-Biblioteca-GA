from django.core.management.base import BaseCommand

from apps.alertas.services import DIAS_AVISO_PREVIO, generar_alertas


class Command(BaseCommand):
    help = "Genera alertas para préstamos por vencer y vencidos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias-aviso-previo",
            type=int,
            default=DIAS_AVISO_PREVIO,
            help=(
                "Días de anticipación para avisar préstamos por vencer "
                f"(por defecto: {DIAS_AVISO_PREVIO})."
            ),
        )

    def handle(self, *args, **options):
        resultado = generar_alertas(
            dias_aviso_previo=options["dias_aviso_previo"]
        )
        self.stdout.write(self.style.SUCCESS(
            f"OK. Nuevas: {resultado['creadas']} · "
            f"Actualizadas: {resultado['actualizadas']} · "
            f"Vencidos detectados: {resultado['vencidos_total']} · "
            f"Por vencer detectados: {resultado['por_vencer_total']}"
        ))
