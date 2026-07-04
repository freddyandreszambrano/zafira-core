let tblScraperSource;

const scraperSource = {
    list() {
        tblScraperSource = Zafira.dataTable('#data', [
            {
                data: 'name',
                render: data => Zafira.escape(data),
            },
            {
                data: 'url',
                render: data => `<a href="${Zafira.escape(data)}" target="_blank" rel="noopener noreferrer" class="text-zafira-primary hover:underline">${Zafira.escape(data)}</a>`,
            },
            {
                data: 'created_at',
                render: data => data ? new Date(data).toLocaleString() : '-',
            },
            {
                data: 'id',
                className: 'text-center',
                orderable: false,
                render: id => Zafira.rowActions(id),
            },
        ], { toggleField: null });
    },
};

$(function () {
    scraperSource.list();
});
